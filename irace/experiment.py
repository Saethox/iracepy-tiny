from typing import Any, Optional


class Experiment:
    """Metadata about the current experiment i.e. target runner execution."""

    configuration_id: str
    instance_id: Optional[str]
    instance: Optional[Any]
    seed: int
    bound: int
    configuration: dict[str, Any]

    def __init__(
            self,
            configuration_id: str,
            instance_id: Optional[str],
            instance: Optional[Any],
            seed: int,
            configuration: dict[str, Any],
    ) -> None:
        self.configuration_id = configuration_id
        self.instance_id = instance_id
        self.seed = seed
        self.instance = instance
        self.configuration = configuration
