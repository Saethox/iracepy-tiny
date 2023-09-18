from abc import ABC
from collections import OrderedDict
from typing import Optional, Iterable, Union, Sequence

import numpy as np


class ParameterSubspace(ABC):

    def __init__(self, name: str, condition: Optional[str]):
        self.name = name
        self.condition = condition

    def format_condition(self) -> str:
        return f"| {self.condition}" if self.condition is not None else ""


class NumericalParameterSubspace(ParameterSubspace, ABC):

    def __init__(
            self,
            name: str,
            lower: Union[float, str, "NumericalParameterSubspace"],
            upper: Union[float, str, "NumericalParameterSubspace"],
            log: bool = False,
            condition: Optional[str] = None
    ) -> None:
        super().__init__(name=name, condition=condition)
        self.lower = lower
        self.upper = upper
        self.log = log

    def format_bound(self, bound: Union[float, str, "NumericalParameterSubspace"]) -> str:
        if isinstance(bound, float):
            return np.format_float_positional(bound, trim='-')
        elif isinstance(bound, str):
            return f'"{bound}"'
        elif isinstance(bound, type(self)):
            return f'"{bound.name}"'
        else:
            return bound

    def _format_line(self, ty: str) -> str:
        lower = self.format_bound(self.lower)
        upper = self.format_bound(self.upper)
        log = ",log" if self.log else ""
        return f'{self.name} "" {ty}{log} ({lower}, {upper}) {self.format_condition()}'


class Real(NumericalParameterSubspace):
    """Real parameters are numerical parameters that can take floating-point values within a given range."""

    def __str__(self) -> str:
        return self._format_line('r')


class Integer(NumericalParameterSubspace):
    """Integer parameters are numerical parameters that can take only integer values within the given range"""

    def __str__(self) -> str:
        return self._format_line('i')


class DiscreteParameterSubspace(ParameterSubspace, ABC):
    def __init__(self, name: str, variants: Sequence, condition: Optional[str] = None):
        super().__init__(name=name, condition=condition)
        self.values = variants

    def _format_line(self, ty: str) -> str:
        return f'{self.name} "" {ty} ({",".join(map(str, range(len(self.values))))}) {self.format_condition()}'


class Categorical(DiscreteParameterSubspace):
    """Categorical parameters are defined by a set of possible values specified as list."""

    def __str__(self) -> str:
        return self._format_line('c')


class Bool(Categorical):
    """Boolean parameters are expressed as categorical parameters with values `True` and `False`."""

    def __init__(self, name: str, condition: Optional[str] = None) -> None:
        super().__init__(name=name, variants=[False, True], condition=condition)


class Ordinal(DiscreteParameterSubspace):
    """
    Ordinal parameters are defined by an ordered set of
    possible values in the same format as for categorical parameters.
    """

    def __str__(self) -> str:
        return self._format_line('o')


class ParameterSpace:
    """A parameter space."""

    params: dict[str, ParameterSubspace]
    forbidden: Optional[Iterable[str]]

    def __init__(self, params: Iterable[ParameterSubspace], forbidden: Optional[Iterable[str]] = None) -> None:
        self.params = OrderedDict([(param.name, param) for param in sorted(params, key=lambda param: param.name)])
        self.forbidden = forbidden

    def __str__(self):
        forbidden = ["[forbidden]", *self.forbidden] if self.forbidden is not None else []
        return '\n'.join([str(param) for param in self.params.values()] + forbidden)

    def get_subspace(self, name: str) -> Optional[ParameterSubspace]:
        return self.params.get(name)
