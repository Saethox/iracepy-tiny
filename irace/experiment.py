from typing import Any, Self

from rpy2.robjects import ListVector

from .scenario import Scenario
from .conversion import rpy2py_recursive
from .params import ParameterSpace, Real, Bool, Integer, Categorical, Ordinal


def repair_configuration(configuration: dict[str, Any], parameter_space: ParameterSpace):
    for name, raw_param in configuration.items():
        subspace = parameter_space.get_subspace(name)

        if isinstance(subspace, Real):
            param = float(raw_param)
        elif isinstance(subspace, Integer):
            param = int(raw_param)
        elif isinstance(subspace, Bool):
            param = bool(int(raw_param))
        elif isinstance(subspace, Categorical) or isinstance(subspace, Ordinal):
            param = subspace.values[int(raw_param)]
        else:
            param = None

        configuration[name] = param


class Experiment:
    """Metadata about the current experiment i.e. target runner execution."""

    configuration_id: str
    instance_id: str
    seed: int
    instance: str
    bound: int
    configuration: dict[str, Any]

    def __init__(
            self,
            configuration_id: str,
            instance_id: str,
            seed: int,
            instance: str,
            configuration: dict[str, Any],
    ) -> None:
        self.configuration_id = configuration_id
        self.instance_id = instance_id
        self.seed = seed
        self.instance = instance
        self.configuration = configuration

    @classmethod
    def rpy2py(cls, obj: ListVector, scenario: Scenario, parameter_space: ParameterSpace) -> Self:
        experiment = rpy2py_recursive(obj)

        configuration_id = str(experiment['id.configuration'])
        seed = int(experiment['seed'])

        if scenario.instances is not None:
            instance_id = str(experiment['id.instance'])
            instance = str(experiment['instance'])
        else:
            instance_id = None
            instance = None

        configuration = experiment['configuration']
        repair_configuration(configuration, parameter_space)

        experiment = Experiment(
            configuration_id=configuration_id,
            instance_id=instance_id,
            seed=seed,
            instance=instance,
            configuration=configuration,
        )

        return experiment
