# Standard Library
import abc
from abc import ABC
from abc import abstractmethod
# from posixpath import split
from typing import (Any, Set, Dict, Type, Tuple, Union, TypeVar, Callable,
                    ClassVar, Iterator, Optional, MutableMapping)
from collections import UserDict

import anyio
from pydantic import Extra
from pydantic import Field
from pydantic import BaseModel
from pydantic import BaseConfig
import pyarrow as pa
from pydantic.main import ModelMetaclass
from pydantic.fields import FieldInfo

from py_svm.core import registry

# from importlib.resources import Resource

_T = TypeVar("_T")


def __dataclass_transform__(
    *,
    eq_default: bool = True,
    order_default: bool = False,
    kw_only_default: bool = False,
    field_descriptors: Tuple[Union[type, Callable[..., Any]], ...] = (()),
) -> Callable[[_T], _T]:
    return lambda a: a


from pydantic.fields import Undefined
from pydantic.typing import resolve_annotations


class DatabaseAPI(MutableMapping[bytes, bytes], ABC):
    """
    A class representing a database.
    """

    @abstractmethod
    def set(self, key: bytes, value: bytes) -> None:
        """
        Assign the ``value`` to the ``key``.
        """
        ...

    @abstractmethod
    def exists(self, key: bytes) -> bool:
        """
        Return ``True`` if the ``key`` exists in the database, otherwise ``False``.
        """
        ...

    @abstractmethod
    def delete(self, key: bytes) -> None:
        """
        Delete the given ``key`` from the database.
        """
        ...


class BaseDB(DatabaseAPI, ABC):
    """
    This is an abstract key/value lookup with all :class:`bytes` values,
    with some convenience methods for databases. As much as possible,
    you can use a DB as if it were a :class:`dict`.
    Notable exceptions are that you cannot iterate through all values or get the length.
    (Unless a subclass explicitly enables it).
    All subclasses must implement these methods:
    __init__, __getitem__, __setitem__, __delitem__
    Subclasses may optionally implement an _exists method
    that is type-checked for key and value.
    """

    @abc.abstractmethod
    def run_query(self, query: str) -> pa.Table:
        ...

    @abc.abstractmethod
    def execute(
        self,
        query: str,
        parameters: object = [],
        multiple_parameter_sets: bool = False,
        *args,
        **kwargs,
    ) -> pa.Table:
        ...

    def set(self, key: bytes, value: bytes) -> None:
        self[key] = value

    def exists(self, key: bytes) -> bool:
        return self.__contains__(key)

    def __contains__(self, key: bytes) -> bool:  # type: ignore # Breaks LSP
        if hasattr(self, "_exists"):
            # Classes which inherit this class would have `_exists` attr
            return self._exists(key)  # type: ignore
        else:
            return super().__contains__(key)

    def delete(self, key: bytes) -> None:
        try:
            del self[key]
        except KeyError:
            pass

    def __getitem__(self, key: bytes) -> bytes:
        ...

    def __setitem__(self, slot: bytes, value: bytes) -> None:
        ...

    def __delitem__(self, key: bytes) -> None:
        ...

    def __iter__(self) -> Iterator[bytes]:
        ...

    def __len__(self) -> int:
        ...

    def _exists(self, key: bytes) -> bool:
        ...


async def long_running_task(index):
    await anyio.sleep(1)
    print(f"Task {index} running...")
    await anyio.sleep(index)
    return f"Task {index} return value"


class Context(UserDict):
    """A context that is injected into every instance of a class that is
    a subclass of `Component`.
    """

    def __init__(self, **kwargs):
        super(Context, self).__init__(**kwargs)
        self.__dict__ = {**self.__dict__, **self.data}

    def __str__(self):
        data = ["{}={}".format(k, getattr(self, k)) for k in self.__slots__]
        return "<{}: {}>".format(self.__class__.__name__, ", ".join(data))


class ContextualizedMixin(object):
    """A mixin that is to be mixed with any class that must function in a
    contextual setting.
    """

    @property
    def context(self) -> Context:
        """Gets the `Context` the object is under.
        Returns
        -------
        `Context`
            The context the object is under.
        """
        return self._context

    @context.setter
    def context(self, context: Context) -> None:
        """Sets the context for the object.
        Parameters
        ----------
        context : `Context`
            The context to set for the object.
        """
        self._context = context


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
        new_cls = super().__new__(cls, name, bases, dict_used, **config_kwargs)
        new_cls.__annotations__ = {
            **pydantic_annotations,
            **new_cls.__annotations__,
        }

        def get_config(name: str) -> Any:
            config_class_value = getattr(new_cls.__config__, name,
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
            instance.__pre_init__(*args, **kwds)
        instance.__init__(*args, **kwds)
        if hasattr(instance, "__post_init__"):
            instance.__post_init__(*args, **kwds)  # type: ignore
        setattr(instance, "context", Context())
        model_type = instance.module_type
        registry.register(instance, model_type)  # type: ignore
        # if model_type is not None:
        return instance


class Module(BaseModel,
             ContextualizedMixin,
             metaclass=InitContext,
             extra=Extra.allow):
    module_type: Optional[str] = ""

    def __post_init__(self) -> None:
        pass

    def __init__(self, **data) -> None:
        super().__init__(**data)

    def get_resource(self, name):
        return registry.get_module("resource", name)

    def modules(self, module_type: str) -> Iterator["Module"]:
        return registry.get_modules(module_type)  # type: ignore

    @property
    def resources(self) -> Dict[str, "Resource"]:
        return list(self.modules("resource"))  # type: ignore

    def __setattr__(self, name: str, value: Any) -> None:
        returned = super().__setattr__(name, value)
        self.log_change(name, value)
        return returned

    def log_change(self, name: str, value: Any) -> None:
        pass


class Resource(Module):
    module_type: str = "resource"


class Behavior(Module):
    module_type: str = "behavior"


class Entity(Module):
    module_type: str = "entity"


class Agent(Module):
    module_type: ClassVar[Optional[str]] = "agent"


# class Clock(Resource):
#     def __init__(self) -> None:
#         super().__init__()

# class Network(Resource):
#     def __init__(self) -> None:
#         super().__init__()
#         self.fake_network = {}

# class AgentEnv(gym.Env, ABC):
#     def __init__(self) -> None:
#         super().__init__()

#     def reset(self):
#         pass

# async def main():
#     from prisma import Prisma

#     db = Prisma()
#     log.success("connecting")
#     await db.connect()

#     env = AgentEnv()
#     network = Network()
#     clock = Clock()

#     await db.disconnect()
#     log.error("disconnecting")

# if __name__ == "__main__":
#     anyio.run(main)
