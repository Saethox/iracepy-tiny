# iracepy-tiny

Pythonic bindings for [irace: Iterated Racing for Automatic Algorithm Configuration](https://github.com/MLopez-Ibanez/irace).

This package is a fork/reimplementation of [`iracepy`](https://github.com/auto-optimization/iracepy) with a reduced
feature set, which tries to be somewhat more pythonic (i.e. define scenarios and parameter spaces dynamically in code,
not in static configuration files).

For more information on `irace`, see its [documentation](https://mlopez-ibanez.github.io/irace/index.html) directly.

If you need any options for `irace` that are not yet implemented here, feel free to open an issue or fork the repository and open a PR.

## Getting Started

### Requirements

- [irace](https://mlopez-ibanez.github.io/irace/#github-development-version) R package (development version, currently [#1fdbba6](https://github.com/MLopez-Ibanez/irace/tree/1fdbba610a263a5dd2372a760d33164809e8495f))
- [Python](https://www.python.org)

Tested with Python 3.12.

### Installation

```shell
pip install git+https://github.com/Saethox/iracepy-tiny#egg=irace
```

### Usage

```python
from irace import irace, ParameterSpace, Scenario, Experiment


def target_runner(experiment: Experiment, scenario: Scenario) -> float:
    ...


parameter_space = ParameterSpace(...)
scenario = Scenario(...)

result = irace.irace(target_runner, parameter_space)
```

## Examples

See the [examples](./examples) directory.