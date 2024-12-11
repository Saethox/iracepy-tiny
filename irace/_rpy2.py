import logging
import math
from collections import OrderedDict
from collections.abc import Mapping, Collection
from typing import Any, Optional

import numpy as np
import pandas as pd
from rpy2 import rinterface, robjects, rinterface_lib
from rpy2.rinterface import SexpClosure, ListSexpVector, rternalize
from rpy2.robjects import ListVector, IntVector, BoolVector, RObject
from rpy2.robjects import numpy2ri, pandas2ri
from rpy2.robjects.packages import importr, PackageNotInstalledError

from . import params as p
from .experiment import Experiment
from .params import ParameterSpace
from .runner import TargetRunner
from .scenario import Scenario

rinterface_lib.callbacks.logger.setLevel(logging.ERROR)  # will display errors, but not warnings

try:
    _irace = importr("irace")
except PackageNotInstalledError as e:
    raise PackageNotInstalledError(
        'The R package irace needs to be installed for this python binding to work. '
        'Consider running `Rscript -e "install.packages(\'irace\', repos=\'https://cloud.r-project.org\')"`'
        ' in your shell. '
        'See more details at https://github.com/mLopez-Ibanez/irace#quick-start') from e

converter = robjects.default_converter + robjects.numpy2ri.converter + robjects.pandas2ri.converter



def rpy2py_recursive(data: Any) -> Any:
    """
    Step through an R object recursively and convert the types to python types as appropriate.
    Leaves will be converted to e.g. numpy arrays or lists as appropriate and the whole tree to a dictionary.
    """
    if data in (rinterface.NULL, rinterface.NA) or isinstance(data, (rinterface_lib.sexp.NACharacterType,)):
        return None
    elif type(data) in [robjects.DataFrame, robjects.ListVector]:
        return OrderedDict(zip(data.names, [rpy2py_recursive(elt) for elt in data]))
    elif type(data) in [robjects.StrVector]:
        if len(data) == 1:
            return rpy2py_recursive(data[0])
        else:
            return [rpy2py_recursive(elt) for elt in data]
    elif type(data) in [robjects.FloatVector, robjects.IntVector, robjects.BoolVector]:
        if len(data) == 1:
            return rpy2py_recursive(data[0])
        else:
            return np.array([rpy2py_recursive(d) for d in data])
    else:
        if hasattr(data, "rclass"):  # An unsupported r class
            raise KeyError(f"conversion for `{type(data)}` is not defined")
        else:
            return data  # We reached the end of recursion


def convert_configuration(raw_configuration: dict[str, Any], parameter_space: ParameterSpace) -> dict[str, Any]:
    """Convert the raw configuration into the appropriate type for the corresponding parameter subspace."""

    configuration = OrderedDict()

    for name, raw_param in raw_configuration.items():
        subspace = parameter_space.get_subspace(name)

        # Ignore unknown metadata keys
        if subspace is None:
            continue

        if raw_param is None or (isinstance(raw_param, float) and math.isnan(raw_param)):
            configuration[name] = None
            continue

        if isinstance(subspace, p.Real):
            param = float(raw_param) if not isinstance(raw_param, rinterface_lib.sexp.NARealType) else None
        elif isinstance(subspace, p.Integer):
            param = int(raw_param) if not isinstance(raw_param, rinterface_lib.sexp.NAIntegerType) else None
        elif isinstance(subspace, p.Bool):
            # `bool` is represented as discrete with `["TRUE", "FALSE"]` variants.
            param = bool(raw_param) if not isinstance(raw_param, rinterface_lib.sexp.NACharacterType) else None
        elif isinstance(subspace, p.Categorical) or isinstance(subspace, p.Ordinal):
            # categorical and ordinal are represented as integers, so we need to convert to the real variant.
            param = subspace.values[int(raw_param)]
        else:
            param = None

        configuration[name] = param

    return configuration


def convert_result(result: pd.DataFrame, parameter_space: ParameterSpace, return_df: bool = False,
                   remove_metadata: bool = True) -> pd.DataFrame | list[dict[str, Any]]:
    if remove_metadata:
        result = result.loc[:, ~result.columns.str.startswith('.')]

    result = [convert_configuration(configuration, parameter_space)
              for configuration in result.to_dict('records')]

    if return_df:
        return pd.DataFrame.from_records(result)
    else:
        return result


def rpy2py_experiment(obj: ListVector, scenario: Scenario, parameter_space: ParameterSpace) -> Experiment:
    experiment = rpy2py_recursive(obj)

    configuration_id = str(experiment['id_configuration'])
    seed = int(experiment['seed'])

    if scenario.instances is not None:
        instance_id = str(experiment['id_instance'])
        instance = scenario.instances[int(experiment['instance'])]
    else:
        instance_id = None
        instance = None

    configuration = convert_configuration(experiment['configuration'], parameter_space)

    experiment = Experiment(
        configuration_id=configuration_id,
        instance_id=instance_id,
        seed=seed,
        instance=instance,
        configuration=configuration,
    )

    return experiment


def py2rpy_expression(value: Any) -> RObject:
    return robjects.r(f'expression({p.check_expression(value)})')


def py2rpy_quote(value: Any) -> RObject:
    return robjects.r(f'quote({p.check_expression(value)})')


def py2rpy_parameter_space(parameter_space: ParameterSpace) -> ListVector:
    r_parameter_space = []
    for subspace in parameter_space.params.values():
        if subspace.condition is not None:
            condition = py2rpy_expression(subspace.condition)
        else:
            condition = True
        if isinstance(subspace, p.Real) or isinstance(subspace, p.Integer):
            constructor = _irace.param_real if isinstance(subspace, p.Real) else _irace.param_int
            lower = py2rpy_expression(subspace.lower)
            upper = py2rpy_expression(subspace.upper)
            transf = "log" if subspace.log else ""
            r_subspace = constructor(name=subspace.name, lower=lower, upper=upper, condition=condition, transf=transf)
        elif isinstance(subspace, p.Bool):
            # `bool` is represented as discrete with `["FALSE", "TRUE"]` variants.
            values = BoolVector([False, True])
            r_subspace = _irace.param_cat(subspace.name, values=values, condition=condition)
        elif isinstance(subspace, p.Categorical) or isinstance(subspace, p.Ordinal):
            # categorical and ordinal are represented as integers.
            values = IntVector(list(range(len(subspace.values))))
            r_subspace = _irace.param_cat(subspace.name, values=values, condition=condition)
        else:
            raise ValueError("unknown parameter type")

        r_parameter_space.append(r_subspace)

    if parameter_space.forbidden is not None:
        forbidden = py2rpy_expression(p.any(*parameter_space.forbidden))
    else:
        forbidden = ''

    return _irace.parametersNew(*r_parameter_space, forbidden=forbidden)


def py2rpy_target_runner(target_runner: TargetRunner, scenario: Scenario,
                         parameter_space: ParameterSpace) -> SexpClosure:
    """Converts a Python `TargetRunner` into an R-callable function that properly converts types."""

    @rternalize
    def inner(experiment: ListSexpVector, _: ListSexpVector) -> ListVector:
        experiment = rpy2py_experiment(ListVector(experiment), scenario, parameter_space)

        try:
            result = target_runner(experiment, scenario)

            if isinstance(result, Collection) and len(result) == 2:
                cost, time = result
                r_result = ListVector(dict(cost=float(cost), time=float(time)))
            elif isinstance(result, Mapping):
                r_result = ListVector({key: float(value) for key, value in result.items()})
            else:
                r_result = ListVector(dict(cost=float(result)))

        except Exception as e:
            r_result = ListVector(dict(cost=math.inf, error=str(e)))

        return r_result

    return inner


def py2rpy_scenario(scenario: Scenario, r_target_runner: SexpClosure,
                    r_parameter_space: Optional[ListVector] = None) -> ListVector:
    r_scenario = {
        'targetRunner': r_target_runner,
        'elitist': int(scenario.elitist),
        'deterministic': int(scenario.deterministic),
        'quiet': int(scenario.verbose == 0),
        'debugLevel': scenario.verbose,
        'parallel': scenario.n_jobs,
    }

    if r_parameter_space is not None:
        r_scenario['parameters'] = r_parameter_space

    if scenario.max_experiments is not None:
        r_scenario['maxExperiments'] = scenario.max_experiments

    if scenario.min_experiments is not None:
        r_scenario['minExperiments'] = scenario.min_experiments

    if scenario.instances is not None and scenario.instances:
        r_scenario['instances'] = list(range(len(scenario.instances)))
    else:
        # Provide a dummy instance
        r_scenario['instances'] = [0]

    if scenario.log_file is not None:
        r_scenario['logFile'] = scenario.log_file
    else:
        r_scenario['logFile'] = ""

    if scenario.exec_dir is not None:
        r_scenario['execDir'] = scenario.exec_dir

    if scenario.seed is not None:
        r_scenario['seed'] = scenario.seed

    return ListVector(r_scenario)
