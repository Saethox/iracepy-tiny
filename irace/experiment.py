from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class Experiment:
    """Metadata about the current experiment, i.e. target runner execution."""

    configuration_id: str
    instance_id: Optional[str]
    instance: Optional[Any]
    seed: int
    configuration: dict[str, Any]
