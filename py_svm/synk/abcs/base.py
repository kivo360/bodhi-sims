# Standard Library
import abc
import uuid
from typing import (Any, Set, cast, Dict, List, Type, Tuple, Union, TypeVar,
                    Callable, ClassVar, Iterator, Optional, MutableMapping)
from pathlib import Path
from itertools import count
# from py_svm.synk.abc import DatabaseAPI
import collections
from contextvars import Context
from contextvars import ContextVar
from contextvars import copy_context

import anyio
from loguru import logger as log
from pydantic import Extra
from pydantic import Field
from pydantic import BaseModel
from pydantic import BaseConfig
from diskcache import Cache
from eth_utils import ValidationError  # type: ignore
from pydantic.main import ModelMetaclass
from eth_utils.toolz import nth  # type: ignore
from eth_utils.toolz import first  # type: ignore
from pydantic.fields import FieldInfo
from pydantic.fields import Undefined
from pydantic.typing import resolve_annotations

from py_svm.core import registry
from py_svm.synk.models import Metadata
from py_svm.utils import dataclass_transform

from .context import UserContext, ContextControl
import devtools as dtoolz
import sqlmodel.main
from typing import (Any, Tuple, Union, TypeVar, Callable)
from functools import wraps
from types import FunctionType
import wrapt

# from importlib.resources import Resource

_T = TypeVar("_T")


@wrapt.decorator
def pass_through(wrapped, instance, args, kwargs):
    return wrapped(*args, **kwargs)


def wrapper(method):

    @wraps(method)
    def wrapped(*args, **kwargs):
        log.warning("Something is here")
        return method(*args, **kwargs)

    return wrapped


def __dataclass_transform__(
    *,
    eq_default: bool = True,
    order_default: bool = False,
    kw_only_default: bool = False,
    field_descriptors: Tuple[Union[type, Callable[..., Any]], ...] = (()),
) -> Callable[[_T], _T]:
    return lambda a: a


@__dataclass_transform__(kw_only_default=True,
                         field_descriptors=(Field, FieldInfo))
class InitContext(ModelMetaclass):

    module_type = None

    def __new__(
        cls,
        name: str,
        bases: Tuple[Type[Any], ...],
        class_dict: Dict[str, Any],
        **kwargs: Any,
    ):
        dict_for_pydantic = {}
        original_annotations = resolve_annotations(
            class_dict.get("__annotations__", {}),
            class_dict.get("__module__", None))
        pydantic_annotations = original_annotations
        # relationship_annotations = {}
        for k, v in class_dict.items():
            dict_for_pydantic[k] = v
        dict_used = {
            **dict_for_pydantic,
            "__weakref__": None,
            "__annotations__": pydantic_annotations,
        }
        # Duplicate logic from Pydantic to filter config kwargs because if they are
        # passed directly including the registry Pydantic will pass them over to the
        # superclass causing an error
        allowed_config_kwargs: Set[str] = {
            key for key in dir(BaseConfig)
            if not (key.startswith("__") and key.endswith("__")
                    )  # skip dunder methods and attributes
        }
        pydantic_kwargs = kwargs.copy()
        config_kwargs = {
            key: pydantic_kwargs.pop(key)
            for key in pydantic_kwargs.keys() & allowed_config_kwargs
        }
        if 'step' in dict_used:
            if callable(dict_used['step']):
                dict_used['step'] = wrapper(dict_used['step'])

        new_cls = super().__new__(cls, name, bases, dict_used, **config_kwargs)
        new_cls.__annotations__ = {
            **pydantic_annotations,
            **new_cls.__annotations__,
        }

        def get_config(name: str) -> Any:
            config_class_value = getattr(
                new_cls.__config__,  # type: ignore
                name,  # type: ignore
                Undefined)  # type: ignore
            if config_class_value is not Undefined:
                return config_class_value
            kwarg_value = kwargs.get(name, Undefined)
            if kwarg_value is not Undefined:
                return kwarg_value
            return Undefined

        return new_cls

    def __call__(cls, *args: Any, **kwds: Any) -> Any:
        instance = cls.__new__(cls, *args, **kwds)
        if hasattr(instance, "__pre_init__"):

            instance.__pre_init__(*args, **kwds)  # type: ignore
        instance.__init__(*args, **kwds)
        if hasattr(instance, "__post_init__"):
            instance.__post_init__(*args, **kwds)  # type: ignore
        setattr(instance, "context", ContextControl())

        model_type = instance.module_type
        registry.register(instance, model_type)  # type: ignore
        # if model_type is not None:
        return instance

    """A mixin that is to be mixed with any class that must function in a
    contextual setting.
    """

    @property
    def context(self) -> ContextControl:
        """Gets the `Context` the object is under.
        Returns
        -------
        `Context`
            The context the object is under.
        """
        return self._context

    @context.setter
    def context(self, context: ContextControl) -> None:
        """Sets the context for the object.
        Parameters
        ----------
        context : `Context`
            The context to set for the object.
        """
        self._context = context


class ModuleBase(BaseModel, metaclass=InitContext, extra=Extra.allow):
    __slots__ = ("__weakref__",)
    module_type: ClassVar[Optional[str]] = ""

    def __post_init__(self, **kwds) -> None:
        pass

    def __pre_init__(self, **kwds) -> None:
        pass

    def __init__(self, **data) -> None:
        super().__init__(**data)


class ResourceBase(ModuleBase):
    module_type: ClassVar[str] = "resource"
