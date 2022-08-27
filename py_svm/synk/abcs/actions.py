import abc
from functools import cached_property
import json
from jinja2 import Template
from pydantic import BaseModel
import inflection
from typing import Dict, List, Optional, ClassVar, Any, Set
from py_svm.synk.abcs.engine import AbstractEngine, SurrealEngine
import torch
import devtools as dvz
from loguru import logger as log
from jinja2 import Environment, PackageLoader

from py_svm.typings import DictAny

jinja_env = Environment(loader=PackageLoader("py_svm", "templates"),
                        trim_blocks=True,
                        lstrip_blocks=True)


class BaseActions(BaseModel, abc.ABC):
    __record_calls__: ClassVar[Set[str]] = {
        'between',
        'check',
        'save',
        'latest',
        'latest_by',
        'many',
        'many_by',
        'save_many',
        'count',
        'find',
        'find_unique',
        'delete_one',
        'delete_many',
        'reset',
        'refresh',
    }

    def is_record(self, name: str) -> bool:
        return name in self.__record_calls__

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"

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


def strip_query(query: str) -> str:
    return query.replace("\n", " ").strip().strip(',')


class DBActions(BaseActions):
    __filterable_fields__ = [
        'context', 'episode_id', 'module_name', 'module_type'
    ]
    # module_name: str
    module_type: str
    timestep: int = -1
    episode_id: str = None

    @property
    def module_name(self) -> str:
        return inflection.tableize(self.__class__.__name__)

    def gettime(self, timestep: int = -1):
        if timestep >= 0:
            self.timestep = timestep
        return timestep

    def template(self, template_name: str) -> Template:
        template_query = jinja_env.get_template(template_name)
        return template_query

    def input_values(self, updates: Dict[str, Any] = {}) -> Dict[str, Any]:
        dd = self.dict(exclude=set(self.__filterable_fields__))
        dd.update(updates)
        return dd

    def update_globals(self, globals: DictAny):
        jinja_env.globals.update(globals)

    def get_query(self,
                  file_name: str,
                  alter: Dict[str, Any] = {},
                  timestep: int = -1) -> str:
        if not self.check():
            raise ValueError(
                "Context is not set: timestep, episode_id, module_name, module_type"
            )
        input_values = self.input_values(alter)
        input_values['timestep'] = self.gettime(timestep)
        input_values['episode_id'] = self.episode_id
        # input_values['module_name'] = self.module_name
        input_values['module_type'] = self.module_type

        latest_item = self.template(file_name)
        query = latest_item.render(module_record=input_values,
                                   module_name=self.module_name)
        query = strip_query(query)
        return query

    def dict(self,
             exclude: Set[str] = set(),
             include: set | dict | None = None,
             by_alias: bool = False,
             exclude_unset: bool = False,
             exclude_defaults: bool = False,
             exclude_none: bool = False) -> Dict[str, Any]:
        exclude.update(self.__filterable_fields__)
        return super().dict(
            exclude=exclude,
            include=include,  # type: ignore
            by_alias=by_alias,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none)

    @property
    def engine(self) -> AbstractEngine:
        return SurrealEngine('http://localhost:8000', 'root', 'root')

    def between(self, start: int, end: int, query: DictAny = {}):
        # Get the time between the start and end timesteps.
        pass

    def check(self) -> bool:
        """Checks that the required context variables are set."""
        if not bool(self.episode_id) or not bool(self.module_type):
            return False

        return True

    def save(self, alter: DictAny = {}):
        """Upserts data along side context"""

        query = self.get_query('save.sur.j2', alter=alter)
        log.info(query)
        # input_values = self.dict(exclude=set(self.__filterable_fields__))
        # input_values.update(alter)
        # # Would create the query here.
        # create_query = jinja_env.get_template('save.sur.j2')
        # module_type = input_values.pop('module_type')
        # query = create_query.render(module_name=module_type,
        #                             module_record=input_values)
        # query = query.replace("\n", " ").strip().strip(',')
        # # query = f"{query};"
        info = self.engine.execute(query)
        return info
        # print(info[0])
        # print(self.__filterable_fields__)

    def latest(self, alter: DictAny = {}):
        input_values = self.dict(exclude=set(self.__filterable_fields__))
        input_values.update(alter)
        # Would create the query here.
        latest_item = jinja_env.get_template('latest.sur.j2')
        module_type = input_values.pop('module_type')
        query = latest_item.render(module_name=module_type)
        query = query.replace("\n", " ").strip().strip(',')

        res = self.engine.execute(query)
        return res

    def latest_by(self, timestep: int = -1, alter: DictAny = {}):
        input_values = self.input_values(alter)
        latest_item = self.template('latest_by.sur.j2')
        query = latest_item.render(module_name=self.module_type,
                                   timestep=self.gettime(timestep))
        query = strip_query(query)
        res = self.engine.execute(query)

        return res

    def many(self, limit: int = 100, alter: DictAny = {}):
        input_values = self.input_values(alter)
        template = self.template('many.sur.j2')
        module_name = input_values.pop('module_type')
        query = strip_query(
            template.render(module_name=module_name, timestep=3, limit=limit))
        res = self.engine.execute(query)
        return res

    def many_by(self,
                limit: int = 100,
                timestep: int = -1,
                alter: DictAny = {}):
        input_values = self.input_values(alter)
        template = self.template('many_by.sur.j2')
        module_name = self.module_type
        query = strip_query(
            template.render(module_name=module_name, timestep=3, limit=limit))
        res = self.engine.execute(query)
        return res

    def save_many(self, data: List[Dict[str, Any]]):

        raise NotImplementedError

    def count(self, alter: Dict[str, Any] = {}) -> int:
        """Gets the total number of records given a query."""
        input_values = self.input_values(alter)
        template = self.template('count.sur.j2')
        module_name = input_values.pop('module_type')
        query_str = strip_query(
            template.render(module_name=module_name, timestep=3))
        res = self.engine.execute(query_str)
        if hasattr(res, "result"):
            return res.result[0]['count']  # type: ignore
        return 0

    def find(self, alter: Dict[str, Any] = {}) -> bool:
        input_values = self.input_values(alter)
        template = self.template('find.sur.j2')
        module_name = input_values.pop('module_type')
        query_str = strip_query(
            template.render(module_name=module_name, timestep=3))
        res = self.engine.execute(query_str)
        return False

    def find_unique(self, alter: Dict[str, Any] = {}) -> bool:
        input_values = self.input_values(alter)
        template = self.template('find_unique.sur.j2')
        module_name = input_values.pop('module_type')
        query_str = strip_query(
            template.render(module_name=module_name, timestep=3))
        res = self.engine.execute(query_str)
        return False

    def delete_one(self, alter: Dict[str, Any] = {}) -> bool:
        input_values = self.input_values(alter)
        template = self.template('delete_one.sur.j2')
        module_name = input_values.pop('module_type')
        query_str = strip_query(
            template.render(module_name=module_name, timestep=3))
        res = self.engine.execute(query_str)
        return False

    def delete_many(self, alter: Dict[str, Any] = {}) -> bool:
        input_values = self.input_values(alter)
        template = self.template('delete_many.sur.j2')
        module_name = input_values.pop('module_type')
        query_str = strip_query(
            template.render(module_name=module_name, timestep=3))
        res = self.engine.execute(query_str)
        return False

    def reset(self):
        """Load the Module State from the database if it exist"""
        raise NotImplementedError

    def refresh(self):
        raise NotImplementedError


def main():
    import uuid
    print(str(uuid.uuid4()))


if __name__ == "__main__":
    main()