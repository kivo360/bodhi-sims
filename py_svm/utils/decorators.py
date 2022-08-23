# Standard Library
# from posixpath import split
from typing import (Any, Tuple, Union, TypeVar, Callable)

# from importlib.resources import Resource

_T = TypeVar("_T")


def dataclass_transform(
    *,
    eq_default: bool = True,
    order_default: bool = False,
    kw_only_default: bool = False,
    field_descriptors: Tuple[Union[type, Callable[..., Any]], ...] = (()),
) -> Callable[[_T], _T]:
    return lambda a: a