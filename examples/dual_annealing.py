from typing import Callable

import numpy as np
from scipy.optimize import dual_annealing

from irace import Experiment, Scenario, ParameterSpace, Real, Bool, irace


def make_objective_function(dim: int = 10) -> Callable:
    def objective_function(x: np.ndarray) -> float:
        return np.sum(x * x - dim * np.cos(2 * np.pi * x)) + dim * np.size(x)

    return objective_function


def make_runner(function: Callable, lower: float = -5.12, upper: float = 5.12, dim: int = 10) -> Callable:
    bounds = list(zip([lower] * dim, [upper] * dim))

    def target_runner(experiment: Experiment) -> float:
        return dual_annealing(function, bounds=bounds, seed=experiment.seed, maxfun=10_000,
                              **experiment.configuration).fun

    return target_runner


params = ParameterSpace([
    Real('initial_temp', 0.02, 5e4, log=True),
    Real('restart_temp_ratio', 1e-4, 1, log=True),
    Real('visit', 1.001, 3),
    Real('accept', -1e3, -5),
    Bool('no_local_search'),
])

dim = 10

scenario = Scenario(
    target_runner=make_runner(make_objective_function(dim), dim=dim),
    instances=[0],
    max_experiments=180,
)

if __name__ == '__main__':
    result = irace(scenario, params)
    print(result)
