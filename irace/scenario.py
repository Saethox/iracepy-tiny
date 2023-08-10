import math
import os
from typing import Optional, Callable, Any, Iterable, TypeAlias

from rpy2.rinterface import SexpClosure, rternalize, ListSexpVector
from rpy2.robjects import ListVector

from ._rpackage import _irace
from .experiment import Experiment

Configuration: TypeAlias = dict[str, Any]
Cost: TypeAlias = float | tuple[float, float] | dict[str, float]
TargetRunner: TypeAlias = Callable[[Experiment], Cost]


class Scenario:
    def __init__(
            self,
            target_runner: TargetRunner,
            max_experiments: int,
            elitist: bool = True,
            instances: Optional[Iterable] = None,
            deterministic: bool = False,
            n_jobs: int = 1,
            seed: Optional[int] = None,
            verbose: int = 0,
    ) -> None:
        self.target_runner = target_runner
        self.max_experiments = max_experiments
        self.elitist = elitist
        self.instances = instances
        self.deterministic = deterministic
        self.n_jobs = n_jobs
        self.seed = seed
        self.verbose = verbose

        self._check()

    def _check(self):
        if self.n_jobs not in (0, 1) and os.name == 'nt':
            raise NotImplementedError(
                'Parallel running on Windows is not supported yet. '
                'Follow https://github.com/auto-optimization/iracepy/issues/16 for updates. '
                'Alternatively, use Linux or MacOS or the irace R package directly.')

    def _py2rpy_target_runner(self) -> SexpClosure:

        @rternalize
        def inner(experiment: ListSexpVector, scenario: ListSexpVector) -> ListVector:
            experiment = Experiment.rpy2py(ListVector(experiment))

            try:
                result = self.target_runner(experiment)
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

    def py2rpy(self) -> (ListVector, SexpClosure):
        r_target_runner = self._py2rpy_target_runner()

        scenario = {
            'targetRunner': r_target_runner,
            'maxExperiments': self.max_experiments,
            'elitist': int(self.elitist),
            'deterministic': int(self.deterministic),
            'quiet': int(self.verbose == 0),
            'debugLevel': self.verbose,
            'parallel': self.n_jobs,
            'logFile': "",
        }

        if self.instances is not None:
            scenario['instances'] = list(self.instances)

        if self.seed is not None:
            scenario['seed'] = self.seed

        return _irace.checkScenario(ListVector(scenario)), r_target_runner
