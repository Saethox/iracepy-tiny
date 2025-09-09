import irace.params as p
from irace import ParameterSpace, Categorical, Ordinal, Real, Integer, Bool, Scenario, Experiment, irace

parameter_space = ParameterSpace([
    Categorical('algorithm', ['as', 'mmas', 'eas', 'ras', 'acs']),
    Ordinal('localsearch', ['0', '1', '2', '3']),
    Real('alpha', 0, 5),
    Real('beta', 0, 10),
    Real('rho', 0.01, 1),
    Integer('ants', 5, 100, log=True),
    Real('q0', 0, 1, condition=p.ValueOf('algorithm').eq('acs')),
    # Dependent upper bounds in integer parameters is currently broken, see https://github.com/MLopez-Ibanez/irace/issues/87.
    # Integer('rasrank', 1, p.ValueOf('ants').min(10), condition=p.ValueOf('algorithm').eq('ras')),
    # Integer('elitistants', 1, p.ValueOf('ants'), condition=p.ValueOf('algorithm').eq('eas')),
    Integer('nnls', 5, 50, condition=p.ValueOf('localsearch').isin(['1', '2', '3'])),
    Bool('dlb', condition=p.ValueOf('localsearch').isin(['1', '2', '3'])),
], forbidden=[p.all(p.ValueOf('alpha').eq(0), p.ValueOf('beta').eq(0))])

scenario = Scenario(
    max_experiments=300,
    verbose=100,
    seed=42,
)


def target_runner(experiment: Experiment, _) -> float:
    return experiment.configuration['alpha'] * experiment.configuration['beta']


if __name__ == '__main__':
    print(parameter_space)
    result = irace(target_runner, parameter_space, scenario, return_df=True)
    print(result)