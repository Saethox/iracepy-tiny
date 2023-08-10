from abc import ABC, abstractmethod
from typing import Optional, Iterable, Union

from rpy2.robjects import ListVector

from ._rpackage import _irace


class Parameter(ABC):

    def __init__(self, name: str, condition: Optional[str]):
        self.name = name
        self.condition = condition

    def format_condition(self) -> str:
        return f"| {self.condition}" if self.condition is not None else ""

    @abstractmethod
    def format_irace(self) -> str:
        pass


class NumericalParameter(Parameter, ABC):

    def __init__(
            self,
            name: str,
            lower: Union[float, str, "NumericalParameter"],
            upper: Union[float, str, "NumericalParameter"],
            log: bool = False,
            condition: Optional[str] = None
    ) -> None:
        super().__init__(name=name, condition=condition)
        self.lower = lower
        self.upper = upper
        self.log = log

    def format_bound(self, bound: Union[float, str, "NumericalParameter"]) -> str:
        if isinstance(bound, float):
            return str(bound).replace('e-0', 'e-').replace('+', '')
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


class Real(NumericalParameter):
    """Real parameters are numerical parameters that can take floating-point values within a given range."""

    def format_irace(self) -> str:
        return self._format_line('r')


class Integer(NumericalParameter):
    """Integer parameters are numerical parameters that can take only integer values within the given range"""

    def format_irace(self) -> str:
        return self._format_line('i')


class DiscreteParameter(Parameter, ABC):
    def __init__(self, name: str, values: Iterable, condition: Optional[str] = None):
        super().__init__(name=name, condition=condition)
        self.values = values

    def _format_line(self, ty: str) -> str:
        return f'{self.name} "" {ty} ({",".join(map(str, self.values))}) {self.format_condition()}'


class Categorical(DiscreteParameter):
    """Categorical parameters are defined by a set of possible values specified as list."""

    def format_irace(self) -> str:
        return self._format_line('c')


class Bool(Integer):
    """Boolean parameters are expressed as an integer parameters with values 0 and 1."""

    def __init__(self, name: str, condition: Optional[str] = None) -> None:
        super().__init__(name=name, lower=0, upper=1, condition=condition)


class Ordinal(DiscreteParameter):
    """
    Ordinal parameters are defined by an ordered set of
    possible values in the same format as for categorical parameters.
    """

    def format_irace(self) -> str:
        return self._format_line('o')


class ParameterSpace:
    """A parameter space."""

    params: Iterable[Parameter]
    forbidden: Optional[Iterable[str]]

    def __init__(self, params: Iterable[Parameter], forbidden: Optional[Iterable[str]] = None) -> None:
        self.params = params
        self.forbidden = forbidden

    def _format_irace(self):
        forbidden = ["[forbidden]", *self.forbidden] if self.forbidden is not None else []
        return '\n'.join([param.format_irace() for param in self.params] + forbidden)

    def py2rpy(self) -> ListVector:
        return _irace.readParameters(text=self._format_irace())
