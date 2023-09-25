import os
from typing import Optional, Sequence


class Scenario:
    """Configuration for irace."""

    def __init__(
            self,
            max_experiments: Optional[int] = None,
            min_experiments: Optional[int] = None,
            instances: Optional[Sequence] = None,
            elitist: bool = True,
            deterministic: bool = False,
            n_jobs: int = 1,
            seed: Optional[int] = None,
            verbose: int = 0,
    ) -> None:
        self.instances = instances
        self.max_experiments = max_experiments
        self.min_experiments = min_experiments
        self.elitist = elitist
        self.deterministic = deterministic
        self.n_jobs = n_jobs
        self.seed = seed
        self.verbose = verbose

        self._check()

    def _check(self):
        if self.n_jobs not in (0, 1) and os.name == 'nt':
            raise NotImplementedError('parallel running on Windows is not supported')

        if self.max_experiments is None and self.min_experiments is None:
            raise ValueError('either `max_experiments` or `min_experiments` needs to be set')
