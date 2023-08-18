import math
from typing import Any, TypeAlias, Protocol

import pandas as pd
from rpy2.rinterface import SexpClosure, ListSexpVector, rternalize
from rpy2.robjects import ListVector

from ._rpackage import _irace
from .conversion import converter
from .experiment import Experiment, repair_configuration
from .params import ParameterSpace
from .scenario import Scenario

Configuration: TypeAlias = dict[str, Any]
Cost: TypeAlias = float | tuple[float, float] | dict[str, float]


class TargetRunner(Protocol):
    def __call__(self, experiment: Experiment, scenario: Scenario) -> Cost: ...


def _py2rpy_target_runner(target_runner: TargetRunner, scenario: Scenario,
                          parameter_space: ParameterSpace) -> SexpClosure:
    @rternalize
    def inner(experiment: ListSexpVector, _: ListSexpVector) -> ListVector:
        experiment = Experiment.rpy2py(ListVector(experiment), scenario, parameter_space)

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


def irace(target_runner: TargetRunner, scenario: Scenario, parameter_space: ParameterSpace, return_df: bool = False,
          remove_metadata: bool = True) -> pd.DataFrame | list[dict[str, Any]]:
    """irace: Iterated Racing for Automatic Algorithm Configuration."""

    r_target_runner = _py2rpy_target_runner(target_runner, scenario, parameter_space)
    r_scenario = scenario.py2rpy(r_target_runner)
    r_params = parameter_space.py2rpy()

    df = _irace.irace(r_scenario, r_params)
    df = converter.rpy2py(df)

    if remove_metadata:
        df = df.loc[:, ~df.columns.str.startswith('.')]

    final_configurations = df.to_dict('records')

    for configuration in final_configurations:
        repair_configuration(configuration, parameter_space)

    if return_df:
        return pd.DataFrame.from_records(final_configurations)
    else:
        return final_configurations
