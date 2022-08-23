import abc
from distutils.log import debug
from pydantic import BaseModel
from typing import Dict, List, Optional, ClassVar, Any
from py_svm.synk.abcs.engine import AbstractEngine
import torch
import devtools as dvz


class BaseActions(BaseModel, abc.ABC):

    processor: AbstractEngine

    class Config:
        arbitrary_types_allowed = True

    @abc.abstractmethod
    def check(self) -> bool:
        """Checks that the required context variables are set."""
        raise NotImplementedError

    @abc.abstractmethod
    def save(self, data: dict):
        """Upserts data along side context"""
        raise NotImplementedError

    @abc.abstractmethod
    def latest(self, query: dict = {}):

        raise NotImplementedError

    @abc.abstractmethod
    def latest_by(self, timestep: int = -1, query_dict: dict = {}):
        """
        > This function returns the latest data point for a given query
        
        :param timestep: The timestep to get the data for
        :type timestep: int
        :param query_dict: A dictionary of key-value pairs that will be used to filter the data
        :type query_dict: dict
        """
        raise NotImplementedError

    @abc.abstractmethod
    def many(self, limit: int = 100):
        """
        > This function raises a NotImplementedError exception
        
        :param limit: The maximum number of items to return, defaults to 100
        :type limit: int (optional)
        """

        raise NotImplementedError

    @abc.abstractmethod
    def many_by(self, timestep: int = -1, query: dict = {}):
        """
        `many_by` returns a list of `self` objects that match the query
        
        :param timestep: The timestep to get the data from. If -1, it will get the latest timestep
        :type timestep: int
        :param query: a dictionary of the query to be used
        :type query: dict
        """
        pass

    @abc.abstractmethod
    def save_many(self, data: List[Dict[str, Any]]):
        raise NotImplementedError

    @abc.abstractmethod
    def count(self, query: Dict[str, Any] = {}) -> int:
        raise NotImplementedError

    @abc.abstractmethod
    def find(self, query: Dict[str, Any] = {}):
        pass

    @abc.abstractmethod
    def find_unique(self, query: Dict[str, Any] = {}):
        pass

    @abc.abstractmethod
    def delete_one(self, query: Dict[str, Any] = {}):
        pass

    @abc.abstractmethod
    def delete_many(self, query: Dict[str, Any] = {}):
        pass


class DBActions(BaseActions):

    def between(self, start: int, end: int, query: dict = {}):
        pass

    def check(self) -> bool:
        """Checks that the required context variables are set."""
        raise NotImplementedError

    def save(self, data: dict):
        """Upserts data along side context"""
        raise NotImplementedError

    def latest(self, query: dict = {}):

        raise NotImplementedError

    def latest_by(self, timestep: int = -1, query_dict: dict = {}):
        raise NotImplementedError

    def many(self, limit: int = 100):
        raise NotImplementedError

    def many_by(self, timestep: int = -1, query: dict = {}):
        pass

    def save_many(self, data: List[Dict[str, Any]]):
        raise NotImplementedError

    def count(self, query: Dict[str, Any] = {}) -> int:
        raise NotImplementedError

    def find(self, query: Dict[str, Any] = {}):
        pass

    def find_unique(self, query: Dict[str, Any] = {}):
        pass

    def delete_one(self, query: Dict[str, Any] = {}):
        pass

    def delete_many(self, query: Dict[str, Any] = {}):
        pass

    def reset(self):
        pass


def main():
    import uuid
    print(str(uuid.uuid4()))


if __name__ == "__main__":
    main()