from typing import Any, Iterable, Optional

import pandas as pd

from .params import ParameterSpace
from .runner import TargetRunner
from .scenario import Scenario


def irace(target_runner: TargetRunner, scenario: Scenario, parameter_space: ParameterSpace, return_df: bool = False,
          remove_metadata: bool = True) -> pd.DataFrame | list[dict[str, Any]]:
    """irace: Iterated Racing for Automatic Algorithm Configuration."""

    from ._rpy2 import _irace, py2rpy_scenario, py2rpy_target_runner, \
        py2rpy_parameter_space, converter, repair_configuration

    r_target_runner = py2rpy_target_runner(target_runner, scenario, parameter_space)
    r_scenario = py2rpy_scenario(scenario, r_target_runner)
    r_params = py2rpy_parameter_space(parameter_space)

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


class IraceRun:
    """A single run of irace with a given target runner, scenario and parameter space."""

    def __init__(self, target_runner: TargetRunner, scenario: Scenario, parameter_space: ParameterSpace,
                 name: Optional[str] = None) -> None:
        self.target_runner = target_runner
        self.scenario = scenario
        self.parameter_space = parameter_space
        self.name = name


def multi_irace(runs: Iterable[IraceRun], n_jobs: int = -1, return_df: bool = False, return_named: bool = False,
                remove_metadata: bool = True) \
        -> list[pd.DataFrame] | list[list[dict[str, Any]]] | dict[str, list[dict[str, Any]]]:
    """Multiple executions of irace in parallel."""

    from joblib import delayed, Parallel

    @delayed
    def inner(run: IraceRun) -> pd.DataFrame | list[dict[str, Any]]:
        result = irace(target_runner=run.target_runner, scenario=run.scenario, parameter_space=run.parameter_space,
                       return_df=return_df, remove_metadata=remove_metadata)
        print(f"A irace run has finished.")
        return result

    results = Parallel(n_jobs=n_jobs)(inner(run) for run in runs)

    if return_named:
        return {run.name if run.name is not None else f"run{i}": result for i, (run, result) in
                enumerate(zip(runs, results))}
    else:
        return list(results)
