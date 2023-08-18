from typing import Callable

import numpy as np
from scipy.optimize import dual_annealing

from irace import Experiment, Scenario, ParameterSpace, Real, Bool, irace


def make_objective_function(dim: int = 10) -> Callable:
    def objective_function(x: np.ndarray) -> float:
        return np.sum(x * x - dim * np.cos(2 * np.pi * x)) + dim * np.size(x)

    return objective_function


def make_runner(lower: float = -5.12, upper: float = 5.12, dim: int = 10) -> Callable:
    bounds = list(zip([lower] * dim, [upper] * dim))

    def inner(experiment: Experiment, scenario: Scenario) -> float:
        return dual_annealing(make_objective_function(dim), bounds=bounds, seed=experiment.seed, maxfun=10_000,
                              **experiment.configuration).fun

    return inner


param_space = ParameterSpace([
    Real('initial_temp', 0.02, 5e4, log=True),
    Real('restart_temp_ratio', 1e-4, 1, log=True),
    Real('visit', 1.001, 3),
    Real('accept', -1e3, -5),
    Bool('no_local_search'),
])

scenario = Scenario(
    max_experiments=180,
    verbose=1,
)

if __name__ == '__main__':
    target_runner = make_runner(dim=10)
    result = irace(target_runner, scenario, param_space, return_df=True)
    print(result)
