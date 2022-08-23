# Standard Library
import abc
from abc import ABC
from abc import abstractmethod
# from posixpath import split
from typing import (Any, Tuple, Union, TypeVar, Callable, Iterator,
                    MutableMapping)

from loguru import logger as log
import pyarrow as pa

# from importlib.resources import Resource


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
    def execute(self,
                query: str,
                parameters: object = [],
                multiple_parameter_sets: bool = False,
                *args,
                **kwargs) -> pa.Table:
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
