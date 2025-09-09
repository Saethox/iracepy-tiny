from abc import ABCMeta, abstractmethod
from collections import OrderedDict
from functools import reduce
from typing import Optional, Iterable, Union, Sequence, Any, Self


class RExpression(metaclass=ABCMeta):
    """An R expression that can be quoted."""

    @abstractmethod
    def to_r_expression(self) -> str:
        pass


def check_expression(value: Any) -> str:
    if isinstance(value, RExpression):
        return value.to_r_expression()
    else:
        return value


class CompositeRExpression(RExpression):

    def __init__(self, left: RExpression, right: RExpression, symbol: str, print_symbol: Optional[str] = None) -> None:
        self.left = left
        self.right = right
        self.symbol = symbol
        self.print_symbol = print_symbol

    def to_r_expression(self) -> str:
        return f"({self.left.to_r_expression()} {self.symbol} {self.right.to_r_expression()})"

    def __str__(self) -> str:
        symbol = self.print_symbol if self.print_symbol is not None else self.symbol
        return f"({self.left} {symbol} {self.right})"


class RCondition(RExpression, metaclass=ABCMeta):

    def both(self, other: Self) -> Self:
        return CompositeRExpression(self, other, symbol='&', print_symbol='and')

    def one(self, other: Self) -> Self:
        return CompositeRExpression(self, other, symbol='|', print_symbol='or')

    def negate(self) -> Self:
        return NegateRCondition(self)


def all(*conditions: RCondition) -> RCondition:
    return reduce(RCondition.both, conditions)


def any(*conditions: RCondition) -> RCondition:
    return reduce(RCondition.one, conditions)


class RawRCondition(RCondition):

    def __init__(self, condition: str) -> None:
        self.condition = condition

    def to_r_expression(self) -> str:
        return self.condition

    def __str__(self) -> str:
        return self.condition

class NegateRCondition(RCondition):

    def __init__(self, condition: RCondition) -> None:
        self.condition = condition

    def to_r_expression(self) -> str:
        return f"(!{self.condition.to_r_expression()})"

    def __str__(self) -> str:
        return f"(!{self.condition})"


class OneOfRCondition(RCondition):
    def __init__(self, name: str, variants: Sequence[str]) -> None:
        self.name = name
        self.variants = variants

    def to_r_expression(self) -> str:
        # Quote string values for R
        quoted_variants = [f'"{v}"' for v in self.variants]
        return f"({self.name} %in% c({', '.join(quoted_variants)}))"

    def __str__(self) -> str:
        return f"({self.name} in [{', '.join(map(str, self.variants))}])"


class ComparisonRCondition(RCondition, CompositeRExpression):
    pass


class RFuncCall(RExpression):

    def __init__(self, symbol: str, *args: RExpression, **kwargs: RExpression) -> None:
        self.symbol = symbol
        self.args = args
        self.kwargs = kwargs

    def to_r_expression(self) -> str:
        str_args = [arg.to_r_expression() for arg in self.args]
        str_kwargs = [f"{name}={value.to_r_expression()}" for name, value in self.kwargs]
        return f"{self.symbol}({', '.join([*str_args, *str_kwargs])})"


class RLiteral(RExpression):

    def __init__(self, value: Any) -> None:
        assert type(value) in (int, float, str, bool)
        self.value = value

    def to_r_expression(self) -> str:
        if isinstance(self.value, str):
            return f'"{self.value}"'
        elif isinstance(self.value, bool):
            return 'TRUE' if self.value else 'FALSE'
        else:
            return str(self.value)

    def __str__(self) -> str:
        return str(self.value) if not isinstance(self.value, str) else f'"{self.value}"'


def check_literal(value: Any) -> RExpression:
    if isinstance(value, RExpression):
        return value
    else:
        return RLiteral(value)


class ValueOf(RExpression):
    """Represents the value of a parameter at runtime."""

    def __init__(self, name: str) -> None:
        self.name = name

    def min(self, other: Any) -> RExpression:
        return RFuncCall('min', self, check_literal(other))

    def max(self, other: Any) -> RExpression:
        return RFuncCall('max', self, check_literal(other))

    def eq(self, value: Any) -> RCondition:
        return ComparisonRCondition(self, check_literal(value), symbol='==')

    def neq(self, value: Any) -> RCondition:
        return ComparisonRCondition(self, check_literal(value), symbol='!=')

    def leq(self, value: Any) -> RCondition:
        return ComparisonRCondition(self, check_literal(value), symbol='<=')

    def geq(self, value: Any) -> RCondition:
        return ComparisonRCondition(self, check_literal(value), symbol='>=')

    def le(self, value: Any) -> RCondition:
        return ComparisonRCondition(self, check_literal(value), symbol='<')

    def ge(self, value: Any) -> RCondition:
        return ComparisonRCondition(self, check_literal(value), symbol='>')

    def inrange(self, lower: Any, upper: Any) -> RCondition:
        return self.ge(lower).both(self.le(upper))

    def isin(self, variants: Sequence[str]) -> RCondition:
        # Ensure variants are strings for categorical comparisons
        return OneOfRCondition(self.name, variants)

    def notin(self, variants: Sequence[str]) -> RCondition:
        return self.isin(variants).negate()

    def to_r_expression(self) -> str:
        return self.name

    def __str__(self) -> str:
        return self.name


class ParameterSubspace(metaclass=ABCMeta):

    def __init__(self, name: str, condition: Optional[str | RCondition]):
        self.name = name
        self.condition = condition

    def _fmt_condition(self):
        return "" if self.condition is None else f"if {self.condition}"


class NumericalParameterSubspace(ParameterSubspace, metaclass=ABCMeta):

    def __init__(
            self,
            name: str,
            lower: Union[float, str | RExpression],
            upper: Union[float, str | RExpression],
            log: bool = False,
            condition: Optional[str | RCondition] = None
    ) -> None:
        super().__init__(name=name, condition=condition)
        self.lower = lower
        self.upper = upper
        self.log = log

    def __str__(self) -> str:
        log = " (log)" if self.log else ""
        return f"{self.name}: ({check_expression(self.lower)}, {check_expression(self.upper)}){log}; {self._fmt_condition()}"


class Real(NumericalParameterSubspace):
    """Real parameters are numerical parameters that can take floating-point values within a given range."""


class Integer(NumericalParameterSubspace):
    """Integer parameters are numerical parameters that can take only integer values within the given range"""


class DiscreteParameterSubspace(ParameterSubspace, metaclass=ABCMeta):
    def __init__(self, name: str, values: Sequence[str], condition: Optional[str | RCondition] = None):
        super().__init__(name=name, condition=condition)
        # Validate that all values are strings
        if not all(isinstance(v, str) for v in values):
            raise TypeError(f"All categorical values must be strings, got: {values}")
        self.values = list(values)  # Convert to list to ensure consistency

    def __str__(self) -> str:
        return f"{self.name}: [{', '.join(self.values)}]; {self._fmt_condition()}"


class Categorical(DiscreteParameterSubspace):
    """Categorical parameters are defined by a set of possible string values."""


class Bool(DiscreteParameterSubspace):
    """Boolean parameters are expressed as categorical parameters with values 'TRUE' and 'FALSE'."""

    def __init__(self, name: str, condition: Optional[str | RCondition] = None) -> None:
        # Use R's boolean string representations
        super().__init__(name=name, values=['FALSE', 'TRUE'], condition=condition)

    def __str__(self) -> str:
        return f"{self.name}: bool; {self._fmt_condition()}"


class Ordinal(DiscreteParameterSubspace):
    """
    Ordinal parameters are defined by an ordered set of
    possible string values in the same format as for categorical parameters.
    """


class ParameterSpace:
    """A parameter space."""

    params: dict[str, ParameterSubspace]
    forbidden: Optional[Iterable[str]]

    def __init__(self, params: Iterable[ParameterSubspace],
                 forbidden: Optional[Iterable[str | RCondition]] = None) -> None:
        self.params = OrderedDict([(param.name, param) for param in params])
        self.forbidden = forbidden

    def __str__(self):
        forbidden = ["[forbidden]", *map(str, self.forbidden)] if self.forbidden is not None else []
        return '\n'.join([*map(str, self.params.values()), *forbidden])

    def get_subspace(self, name: str) -> Optional[ParameterSubspace]:
        return self.params.get(name)