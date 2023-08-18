import os
from typing import Optional, Sequence

from rpy2.rinterface import SexpClosure
from rpy2.robjects import ListVector

from ._rpackage import _irace


class Scenario:
    """Configuration for irace."""

    def __init__(
            self,
            max_experiments: int,
            instances: Optional[Sequence] = None,
            elitist: bool = True,
            deterministic: bool = False,
            n_jobs: int = 1,
            seed: Optional[int] = None,
            verbose: int = 0,
    ) -> None:
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
            raise NotImplementedError('parallel running on Windows is not supported')

    def py2rpy(self, target_runner: SexpClosure) -> ListVector:
        scenario = {
            'targetRunner': target_runner,
            'maxExperiments': self.max_experiments,
            'elitist': int(self.elitist),
            'deterministic': int(self.deterministic),
            'quiet': int(self.verbose == 0),
            'debugLevel': self.verbose,
            'parallel': self.n_jobs,
            'logFile': "",
        }

        if self.instances is not None and len(self.instances) > 0:
            scenario['instances'] = list(self.instances)
        else:
            scenario['instances'] = [0]

        if self.seed is not None:
            scenario['seed'] = self.seed

        return _irace.checkScenario(ListVector(scenario))
