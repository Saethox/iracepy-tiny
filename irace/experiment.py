from typing import Any, Self

from rpy2.robjects import ListVector

from .conversion import rpy2py_recursive


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
    def rpy2py(cls, obj: ListVector) -> Self:
        experiment = rpy2py_recursive(obj)

        experiment = Experiment(
            configuration_id=str(experiment['id.configuration']),
            instance_id=str(experiment['id.instance']),
            seed=int(experiment['seed']),
            instance=str(experiment['instance']),
            configuration=experiment['configuration'],
        )

        return experiment
