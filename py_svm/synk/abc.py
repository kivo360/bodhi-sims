import abc
from abc import ABC, abstractmethod
from collections import UserDict

# from importlib.resources import Resource

# from posixpath import split
from turtle import forward
from typing import (
    Any,
    Callable,
    ClassVar,
    ContextManager,
    Dict,
    FrozenSet,
    Generator,
    Hashable,
    Iterable,
    Iterator,
    List,
    MutableMapping,
    NamedTuple,
    Optional,
    OrderedDict,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)

import gym
import pyarrow as pa
from py_svm.typings import ReprArgs
from py_svm.utils import hooks
from py_svm.utils.hooks import RemovableHandle
from pydantic import fields
from pydantic import main as mainpydantic
from pydantic import mypy
from pydantic.main import ModelMetaclass
from py_svm import log

# from sqlalchemy.orm import registry
import weakref
from py_svm.core import registry

T = TypeVar("T", bound="Module")


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


class InitContext(abc.ABCMeta):
    def __call__(cls, *args, **kwargs):

        instance = cls.__new__(cls, *args, **kwargs)
        setattr(instance, "context", Context())
        instance.__init__(*args, **kwargs)
        return instance


class Module(ABC, ContextualizedMixin, metaclass=InitContext):
    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        return

    def __init__(self) -> None:
        super().__init__()


_resource_registry = {}


class Resource(Module):
    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        _resource_registry[cls.__name__] = cls
        return

    @property
    def resources(self) -> Dict[str, "Resource"]:
        return _resource_registry


class ClockResource(Resource):
    def __init__(self) -> None:
        super().__init__()

    # def __call__(self) -> "Clock":
    #     return Clock()


class AgentEnv(gym.Env, ABC):
    def __init__(self) -> None:
        super().__init__()

    def reset(self):
        pass


def main():
    env = AgentEnv()

    # env = Resource()
    # log.success(env.resources)
    log.info(env)

    # for name, resource in env.named_resources():
    #     print((name, resource))

    # print(env.resources)
    # net = TestApplyInherit()
    # for name, child in net.named_children():
    #     print((name, child))
    # print("hello world")


if __name__ == "__main__":
    main()
