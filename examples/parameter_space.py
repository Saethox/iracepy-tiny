from irace import *

if __name__ == '__main__':
    parameter_space = ParameterSpace([
        Categorical('algorithm', ['as', 'mmas', 'eas', 'ras', 'acs']),
        Categorical('localsearch', [0, 1, 2, 3]),
        Real('alpha', 0, 5),
        Real('beta', 0, 10),
        Real('rho', 0.01, 1),
        Integer('ants', 5, 100),
        Integer('nnls', 5, 50),
        Real('q0', 0, 1),
        Bool('dlb'),
        Integer('rasrank', 1, "ants"),
        Integer('elistants', 1, 750),
    ])

    print(parameter_space.py2rpy())
