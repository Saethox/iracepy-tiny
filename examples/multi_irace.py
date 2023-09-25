from typing import Callable

import numpy as np
from scipy.optimize import dual_annealing, differential_evolution

from irace import Experiment, Scenario, ParameterSpace, Real, Bool, Categorical, Run, \
    multi_irace


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


def target_runner1(experiment: Experiment, scenario: Scenario) -> float:
    res = dual_annealing(
        experiment.instance,
        bounds=experiment.instance.bounds,
        seed=experiment.seed,
        maxfun=10_000,
        **experiment.configuration
    )
    return res.fun


def target_runner2(experiment: Experiment, scenario: Scenario) -> float:
    mutation_max = experiment.configuration.pop("mutation_max")
    mutation_min = experiment.configuration.pop("mutation_min_ratio") * mutation_max
    experiment.configuration['mutation'] = (mutation_min, mutation_max)

    res = differential_evolution(
        experiment.instance,
        bounds=experiment.instance.bounds,
        seed=experiment.seed,
        maxiter=80,
        **experiment.configuration
    )
    return res.fun


parameter_space1 = ParameterSpace([
    Real('initial_temp', 0.02, 5e4, log=True),
    Real('restart_temp_ratio', 1e-4, 1, log=True),
    Real('visit', 1.001, 3),
    Real('accept', -1e3, -5),
    Bool('no_local_search'),
])

parameter_space2 = ParameterSpace([
    Categorical('strategy',
                ['best1bin', 'best1exp', 'rand1exp', 'randtobest1exp', 'currenttobest1exp', 'best2exp', 'rand2exp',
                 'randtobest1bin', 'currenttobest1bin', 'best2bin', 'rand2bin', 'rand1bin']),
    Real('mutation_max', 0, 2),
    Real('mutation_min_ratio', 0, 1),
    Real('recombination', 0, 1),
    Bool('polish'),
])

scenario = Scenario(
    max_experiments=180,
    instances=[Rastrigin(dim) for dim in (2, 3, 5, 10, 20, 40)],
    verbose=0,
)

if __name__ == '__main__':
    run1 = Run(target_runner1, scenario, parameter_space1, name='dual_annealing')
    run2 = Run(target_runner2, scenario, parameter_space2, name='differential_evolution')

    results = multi_irace([run1, run2], return_named=True, return_df=True, n_jobs=2, global_seed=42)

    for name, result in results.items():
        print(f"--- Tuning result for {name} ---")
        print(result)
