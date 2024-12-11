from typing import Any, Iterable, Optional

import pandas as pd

from .params import ParameterSpace
from .runner import TargetRunner
from .scenario import Scenario


def irace(target_runner: TargetRunner, parameter_space: ParameterSpace, scenario: Scenario, return_df: bool = False,
          remove_metadata: bool = True) -> pd.DataFrame | list[dict[str, Any]]:
    """irace: Iterated Racing for Automatic Algorithm Configuration."""

    from ._rpy2 import _irace, py2rpy_scenario, py2rpy_target_runner, py2rpy_parameter_space, converter, convert_result

    r_target_runner = py2rpy_target_runner(target_runner, scenario, parameter_space)
    r_parameter_space = py2rpy_parameter_space(parameter_space)
    r_scenario = py2rpy_scenario(scenario, r_target_runner, r_parameter_space)

    result = _irace.irace(r_scenario)
    result = converter.rpy2py(result)

    return convert_result(result, parameter_space, return_df=return_df, remove_metadata=remove_metadata)


class Run:
    """A single run of irace with a given target runner and scenario."""

    def __init__(self, target_runner: TargetRunner, parameter_space: ParameterSpace, scenario: Scenario,
                 name: Optional[str] = None) -> None:
        self.target_runner = target_runner
        self.parameter_space = parameter_space
        self.scenario = scenario
        self.name = name


def multi_irace(runs: Iterable[Run], n_jobs: int = 1, return_df: bool = False, return_named: bool = False,
                remove_metadata: bool = True, global_seed: Optional[int] = None, joblib: bool = False) \
        -> list[pd.DataFrame] | list[list[dict[str, Any]]] | dict[str, list[dict[str, Any]]]:
    """Multiple executions of irace in parallel."""

    if joblib:
        from joblib import delayed, Parallel

        @delayed
        def inner(run: Run) -> pd.DataFrame | list[dict[str, Any]]:
            return irace(target_runner=run.target_runner, scenario=run.scenario, parameter_space=run.parameter_space,
                         return_df=return_df, remove_metadata=remove_metadata)

        results = Parallel(n_jobs=n_jobs)(inner(run) for run in runs)
    else:
        from ._rpy2 import py2rpy_scenario, py2rpy_target_runner, py2rpy_parameter_space, _irace, ListVector, converter, \
            convert_result
        from multiprocessing import cpu_count

        if n_jobs < 0:
            parallel = cpu_count() + 1 + n_jobs
        else:
            parallel = n_jobs
        parallel = max(parallel, 1)

        r_target_runners = [py2rpy_target_runner(run.target_runner, run.scenario, run.parameter_space) for run in runs]
        r_scenarios = ListVector([(i, py2rpy_scenario(run.scenario, r_target_runner))
                                  for i, (run, r_target_runner) in enumerate(zip(runs, r_target_runners))])
        r_parameter_spaces = ListVector([(i, py2rpy_parameter_space(run.parameter_space))
                                         for i, run in enumerate(runs)])

        results = _irace.multi_irace(r_scenarios, r_parameter_spaces, parallel=parallel, global_seed=global_seed)
        results = converter.rpy2py(results)

        results = [convert_result(converter.rpy2py(result), run.parameter_space)
                   for run, (_, result) in zip(runs, results.items())]

    if return_named:
        return {run.name if run.name is not None else f"run{i}": result
                for i, (run, result) in enumerate(zip(runs, results))}
    else:
        return list(results)
