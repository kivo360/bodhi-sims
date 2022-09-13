# Standard Library
# import torch.nn.modules.module
from typing import (Any, Set, cast, Dict, Type, Tuple, Union, TypeVar, Callable,
                    ClassVar, Optional)
from functools import wraps
# from py_svm.synk.abc import DatabaseAPI
import collections

import orjson
from pydantic import Extra
from pydantic import Field
from pydantic import BaseModel
from pydantic import BaseConfig
from eth_utils import ValidationError  # type: ignore
from pydantic.main import ModelMetaclass
from eth_utils.toolz import nth  # type: ignore
from eth_utils.toolz import first  # type: ignore
from pydantic.fields import FieldInfo
from pydantic.fields import Undefined
from pydantic.typing import resolve_annotations
from eth_utils.decorators import combomethod

from py_svm.core import registry

from .context import ContextControl

# from torch.nn.modules.module

_T = TypeVar("_T")


def isattr(obj: object, name: str) -> bool:
    return bool(getattr(obj, name, None))


def step_wrapper(method):

    @wraps(method)
    def wrapped(*args, **kwargs):

        self = args[0]
        input: Tuple[Any, ...] | None = None
        stripped_args = args[1:]
        if self._step_pre_hooks:
            input = cast(tuple, self._run_pre_hooks(*stripped_args, **kwargs))
        if not input:
            input = stripped_args
        result = method(self, *input, **kwargs)
        result = self._run_hooks(result, *input, **kwargs)
        return result

    return wrapped


def orjson_dumps(v, *, default):
    # orjson.dumps returns bytes, to match standard json.dumps we need to decode
    return orjson.dumps(v, default=default).decode()


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
    """
    A mixin that is to be mixed with any class that must function in a
    contextual setting.
    """
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
                dict_used['step'] = step_wrapper(dict_used['step'])

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

        if isattr(instance, "__pre_init__"):
            instance.__pre_init__(*args, **kwds)  # type: ignore
        instance.__init__(*args, **kwds)
        if isattr(instance, "__post_init__"):
            instance.__post_init__(*args, **kwds)  # type: ignore
        setattr(instance, "context", ContextControl())

        model_type = instance.module_type

        registry.register(instance, model_type)  # type: ignore
        # if model_type is not None:
        return instance

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


class ModuleBase(BaseModel, metaclass=InitContext):
    """A base class for all modules. Use to define common attributes and"""

    __slots__ = ("__weakref__",)
    __modules__ = {}
    _step_hooks: Dict[str, Callable] = collections.OrderedDict()
    _step_pre_hooks: Dict[str, Callable] = collections.OrderedDict()
    _forward_hooks: Dict[str, Callable] = collections.OrderedDict()
    _forward_pre_hooks: Dict[str, Callable] = collections.OrderedDict()
    # _state_dict_hooks: Dict[int, Callable] = collections.OrderedDict()
    # _load_state_dict_pre_hooks: Dict[int, Callable] = collections.OrderedDict()
    # _load_state_dict_post_hooks: Dict[int, Callable] = collections.OrderedDict()
    # _non_persistent_buffers_set: Dict[int, Callable] = collections.OrderedDict()
    # _is_full_backward_hook: Dict[int, Callable] = collections.OrderedDict()

    module_type: ClassVar[Optional[str]] = ""

    @combomethod
    def get_name(combo) -> str:
        if isinstance(combo, type):
            # This is a classmethod, so return the class name directly.
            return combo.__name__
        elif isinstance(combo, ModuleBase):
            # Get the name as an instance.
            return combo.__class__.__name__
        else:
            raise TypeError("Unknown type")

    def __init__(self, **data) -> None:
        super().__init__(**data)

    def _run_pre_hooks(self, *args, **kwds) -> Tuple[Any, ...]:
        _input = None
        for hook in self._step_pre_hooks.values():
            _input = hook(self, *args, **kwds)
        if isinstance(_input, (tuple, list, set)):
            return tuple(_input)
        return _input,

    def _run_hooks(self, result, *args, **kwds) -> Tuple[Any, ...]:
        for hook in self._step_hooks.values():
            result = hook(self, result, *args, **kwds)

        return result

    class Config:
        extra: Extra = Extra.allow
        arbitrary_types_allowed: bool = True
        json_loads = orjson.loads
        json_dumps = orjson_dumps
        smart_union: bool = True


class ResourceBase(ModuleBase):
    module_type: str = "resource"

    def reset(self):
        # Load resouirce state given available selection data
        pass

    def refresh(self):
        """Refreshes the resource state. Use function call automatically using callback. Different from `reset` function."""
        pass