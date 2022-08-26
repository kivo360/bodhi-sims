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

from .context import UserContext, ContextualizedMixin, ContextControl
import devtools as dtoolz


@dataclass_transform(kw_only_default=True, field_descriptors=(Field, FieldInfo))
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
        pydantic_annotations = {}
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
        processor = dict_used.pop('processor', None)
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

        # if processor is not None:
        #     log.info(processor)
        # dict_fields = new_cls.__dict__.get('__fields__', {})
        # model_field = dict_fields.get('processor')
        # model_field.default = processor
        # log.info(model_field)

        # log.debug(new_cls.__dict__)
        # if 'processor' in new_cls.__dict__.get('__fields__', {}):
        #     new_cls.__dict__['__fields__']['processor'].default = processor
        # log.warning(new_cls.__dict__.get("__fields__", {}))
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


@dataclass_transform(kw_only_default=True, field_descriptors=(Field, FieldInfo))
class ModuleBase(BaseModel,
                 ContextualizedMixin,
                 metaclass=InitContext,
                 extra=Extra.allow):
    module_type: ClassVar[Optional[str]] = ""

    def __post_init__(self, **kwds) -> None:
        pass

    def __pre_init__(self, **kwds) -> None:
        pass

    def __init__(self, **data) -> None:
        super().__init__(**data)


class ResourceBase(ModuleBase):
    module_type: ClassVar[str] = "resource"
