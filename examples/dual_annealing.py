from typing import Callable

import numpy as np
from scipy.optimize import dual_annealing

from irace import Experiment, Scenario, ParameterSpace, Real, Bool, irace


class Instance(Callable):
    dim: int

    def __init__(self, dim: int):
        self.dim = dim


class Rastrigin(Instance):
    def __init__(self, dim: int, lower: float = -5.12, upper: float = 5.12):
        super().__init__(dim=dim)
        self.lower = lower
        self.upper = upper

    def __call__(self, x: np.ndarray) -> float:
        return np.sum(x * x - self.dim * np.cos(2 * np.pi * x)) + self.dim * np.size(x)

    @property
    def bounds(self) -> list:
        return list(zip([self.lower] * self.dim, [self.upper] * self.dim))


def target_runner(experiment: Experiment, scenario: Scenario) -> float:
    res = dual_annealing(
        experiment.instance,
        bounds=experiment.instance.bounds,
        seed=experiment.seed,
        maxfun=10_000,
        **experiment.configuration
    )
    return res.fun


parameter_space = ParameterSpace([
    Real('initial_temp', 0.02, 5e4, log=True),
    Real('restart_temp_ratio', 1e-4, 1, log=True),
    Real('visit', 1.001, 3),
    Real('accept', -1e3, -5),
    Bool('no_local_search'),
])

scenario = Scenario(
    max_experiments=180,
    instances=[Rastrigin(dim) for dim in (2, 3, 5, 10, 20, 40)],
    verbose=100,
    seed=42,
)

if __name__ == '__main__':
    result = irace(target_runner, parameter_space, scenario, return_df=True)
    print(result)
