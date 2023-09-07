import logging
import math
from collections import OrderedDict
from typing import Any

import numpy as np
from rpy2 import rinterface, robjects, rinterface_lib
from rpy2.rinterface import SexpClosure, ListSexpVector, rternalize
from rpy2.robjects import ListVector
from rpy2.robjects import numpy2ri, pandas2ri
from rpy2.robjects.packages import importr, PackageNotInstalledError

from .experiment import Experiment
from .params import ParameterSpace, Real, Integer, Bool, Categorical, Ordinal
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

    if data == rinterface.NULL:
        return None
    elif data == rinterface.na_values.NA_Character:
        return None
    elif type(data) in [robjects.DataFrame, robjects.ListVector]:
        return OrderedDict(zip(data.names, [rpy2py_recursive(elt) for elt in data]))
    elif type(data) in [robjects.StrVector]:
        if len(data) == 1:
            return rpy2py_recursive(data[0])
        else:
            return [rpy2py_recursive(elt) for elt in data]
    elif type(data) in [robjects.FloatVector, robjects.IntVector]:
        if len(data) == 1:
            return rpy2py_recursive(data[0])
        else:
            return np.array(data)
    else:
        if hasattr(data, "rclass"):  # An unsupported r class
            raise KeyError(f"conversion for `{type(data)}` is not defined")
        else:
            return data  # We reached the end of recursion


def repair_configuration(configuration: dict[str, Any], parameter_space: ParameterSpace):
    """Convert the raw configuration into the appropriate type for the corresponding parameter subspace."""

    for name, raw_param in configuration.items():
        subspace = parameter_space.get_subspace(name)

        # Ignore unknown metadata keys
        if subspace is None:
            continue

        if isinstance(subspace, Real):
            param = float(raw_param)
        elif isinstance(subspace, Integer):
            param = int(raw_param)
        elif isinstance(subspace, Bool):
            # `bool` is represented as discrete with `["0", "1"]` variants.
            param = bool(int(raw_param))
        elif isinstance(subspace, Categorical) or isinstance(subspace, Ordinal):
            # categorical and ordinal are represented as integers, so we need to convert to the real variant.
            param = subspace.values[int(raw_param)]
        else:
            param = None

        configuration[name] = param


def rpy2py_experiment(obj: ListVector, scenario: Scenario, parameter_space: ParameterSpace) -> Experiment:
    experiment = rpy2py_recursive(obj)

    configuration_id = str(experiment['id.configuration'])
    seed = int(experiment['seed'])

    if scenario.instances is not None:
        instance_id = str(experiment['id.instance'])
        instance = scenario.instances[int(experiment['instance'])]
    else:
        instance_id = None
        instance = None

    configuration = experiment['configuration']
    repair_configuration(configuration, parameter_space)

    experiment = Experiment(
        configuration_id=configuration_id,
        instance_id=instance_id,
        seed=seed,
        instance=instance,
        configuration=configuration,
    )

    return experiment


def py2rpy_parameter_space(parameter_space: ParameterSpace) -> ListVector:
    return _irace.readParameters(text=str(parameter_space))


def py2rpy_target_runner(target_runner: TargetRunner, scenario: Scenario,
                         parameter_space: ParameterSpace) -> SexpClosure:
    """Converts a Python `TargetRunner` into an R-callable function that properly converts types."""

    @rternalize
    def inner(experiment: ListSexpVector, _: ListSexpVector) -> ListVector:
        experiment = rpy2py_experiment(ListVector(experiment), scenario, parameter_space)

        try:
            result = target_runner(experiment=experiment, scenario=scenario)
        except Exception as e:
            return ListVector(dict(cost=math.inf, error=str(e)))

        if isinstance(result, float):
            return ListVector(dict(cost=float(result)))
        elif isinstance(result, tuple):
            cost, time = result
            return ListVector(dict(cost=float(cost), time=float(time)))
        elif isinstance(result, dict):
            return ListVector({key: float(value) for key, value in result.items()})
        else:
            raise NotImplementedError("`target_runner` returned an invalid result")

    return inner


def py2rpy_scenario(scenario: Scenario, r_target_runner: SexpClosure) -> ListVector:
    r_scenario = {
        'targetRunner': r_target_runner,
        'maxExperiments': scenario.max_experiments,
        'minExperiments': scenario.min_experiments,
        'elitist': int(scenario.elitist),
        'deterministic': int(scenario.deterministic),
        'quiet': int(scenario.verbose == 0),
        'debugLevel': scenario.verbose,
        'parallel': scenario.n_jobs,
        'logFile': "",
    }

    if scenario.instances is not None and scenario.instances:
        r_scenario['instances'] = list(range(len(scenario.instances)))
    else:
        # Provide a dummy instance
        r_scenario['instances'] = [0]

    if scenario.seed is not None:
        r_scenario['seed'] = scenario.seed

    return _irace.checkScenario(ListVector(r_scenario))
