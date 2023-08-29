from typing import Protocol, TypeAlias

from .scenario import Scenario
from .experiment import Experiment

Cost: TypeAlias = float | tuple[float, float] | dict[str, float]


class TargetRunner(Protocol):
    """A runner that executes the target algorithm with the given configuration and experiment data."""

    def __call__(self, experiment: Experiment, scenario: Scenario) -> Cost: ...
