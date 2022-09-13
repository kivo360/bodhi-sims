# Standard Library
import abc
import uuid
from typing import Any, ClassVar, Dict, List, Set
from decimal import Decimal
import datetime

from jinja2 import Template
from jinja2 import Environment
from jinja2 import PackageLoader
from loguru import logger as log
from pydantic import BaseModel, Field
import inflection
from py_svm.utils import isattr

from py_svm.typings import DictAny
from py_svm.synk.abcs.engine import BaseResponse, SurrealEngine
from py_svm.synk.abcs.engine import AbstractEngine

jinja_env = Environment(loader=PackageLoader("py_svm", "templates"),
                        trim_blocks=True,
                        lstrip_blocks=True)

ACTIVE_ENGINE: AbstractEngine = None


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
        'context', 'episode', 'module_name', 'module_type', 'get_name'
    ]
    # module_name: str
    module_type: str = 'db'
    timestep: int = 0
    episode: str | None = None

    @property
    def module_name(self) -> str:
        return inflection.tableize(self.__class__.__name__)

    def gettime(self, timestep: int = -1):
        if timestep >= 0:
            self.timestep = timestep
        return self.timestep

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
        # I so want to make this faster. Rust all day and night baby!
        if not self.check():
            raise ValueError(
                "Context is not set: timestep, episode_id, module_name, module_type"
            )
        input_values = self.input_values(alter)
        input_values['timestep'] = self.gettime(timestep)
        input_values['episode'] = self.episode
        # input_values['module_name'] = self.module_name
        input_values['module_type'] = self.module_type

        latest_item = self.template(file_name)
        query = latest_item.render(
            module_record=self.get_input_str(input_values),
            module_name=self.module_name)
        query = strip_query(query)
        return query

    def get_input_str(self, input_vals: dict, join_key: str = ', ') -> str:
        input_list = []
        for key, value in input_vals.items():
            if isinstance(value, (str, uuid.UUID)):
                input_list = input_list + [f"{key}='{str(value)}'"]
            elif isinstance(value, (int, float, Decimal)):
                input_list = input_list + [f"{key}={value}"]
            elif isinstance(value, bool):
                input_list = input_list + [f"{key}={str(value).lower()}"]
            elif isinstance(value, (datetime.datetime, datetime.date)):
                input_list = input_list + [f"{key}='{value.isoformat()}'"]
            elif isinstance(value, dict):
                input_list = input_list + [f'{{{self.get_input_str(value)}}}']
            elif isinstance(value, list):
                _local_list = [self.get_input_str(item) for item in value]
                separated = ',\n'.join(_local_list)
                input_list = input_list + [f"[{separated}]"]
            else:
                input_list = input_list + [f"{key}='{str(value)}'"]
        return join_key.join(input_list)

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
        global ACTIVE_ENGINE
        if not ACTIVE_ENGINE:
            ACTIVE_ENGINE = SurrealEngine('http://localhost:8000', 'root',
                                          'root')
        return ACTIVE_ENGINE

    def between(self, start: int, end: int, query: DictAny = {}):
        # Get the time between the start and end timesteps.
        pass

    def check(self) -> bool:
        """Checks that the required context variables are set."""
        if not bool(self.episode) or not bool(self.module_type):
            return False

        return True

    def save(self, alter: DictAny = {}) -> BaseResponse:
        """Upserts data along side context"""

        query: str = self.get_query('save.sur.j2', alter=alter)
        # log.info(query)
        info: 'BaseResponse' = self.engine.execute(query)
        return info

    def latest(self, alter: DictAny = {}):
        input_values = self.dict(exclude=set(self.__filterable_fields__))
        input_values.update(alter)
        # Would create the query here.
        latest_item: Template = jinja_env.get_template('latest.sur.j2')

        module_type: str = self.module_type
        # log.warning(module_type)
        query: str = latest_item.render(module_name=self.module_name)
        query: str = query.replace("\n", " ").strip().strip(',')
        res: 'BaseResponse' = self.engine.execute(query)
        return res

    def latest_by(self,
                  timestep: int = -1,
                  alter: DictAny = {}) -> 'BaseResponse':
        input_values: Dict[str, Any] = self.input_values(alter)
        # Can possibly add a group_by here. The groupby would be a list of fields (in string form) to group by.
        # Run a few practice queries in the database to see how this works.
        latest_item: Template = self.template('latest_by.sur.j2')
        query: str = latest_item.render(module_name=self.module_type,
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
        # input_values = self.input_values(alter)
        input_values = {
            'episode': self.episode,
            'module_type': self.module_type
        }
        template = self.template('count.sur.j2')
        module_name = self.module_name
        query_str = strip_query(
            template.render(module_name=module_name,
                            timestep=self.gettime(self.timestep),
                            where_by=self.get_input_str(input_values, ' and ')))
        res = self.engine.execute(query_str)
        if res.success():
            # print(res)
            if not res.empty():
                return res.first().get('count', 0)  # type: ignore

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

    def refresh(self):
        raise NotImplementedError


def main():
    # Standard Library
    import uuid
    print(str(uuid.uuid4()))


if __name__ == "__main__":
    main()
