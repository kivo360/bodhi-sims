# from posixpath import split
# Standard Library
from typing import (Any, Set, Dict, Type, Tuple, Union, TypeVar, Callable,
                    ClassVar, Iterator, Optional)

from loguru import logger as log
from pydantic import Extra
from pydantic import Field
from pydantic import BaseModel
from pydantic import BaseConfig
from pydantic.main import ModelMetaclass
from pydantic.fields import FieldInfo
from pydantic.fields import Undefined
from pydantic.typing import resolve_annotations

from py_svm.core import registry
from py_svm.synk.abcs.engine import AbstractEngine, SurrealEngine
from py_svm.utils import dataclass_transform

from .abcs.context import UserContext

from py_svm.synk.abcs.base import ModuleBase, ResourceBase
from py_svm.synk.abcs.actions import DBActions

from py_svm.utils import dataclass_transform
from pydantic.fields import Field, FieldInfo


class Module(ModuleBase, DBActions):
    module_type = "module"
    timestep: int = 0
    __modules__ = {}

    @property
    def resources(self) -> Dict[str, "ResourceBase"]:
        """
        > This function returns a weakref value dictionary of all the resources in the project
        :return: A dictionary of all the resources in the project.
        """
        return list(self.modules("resource"))  # type: ignore

    def get_resource(self, name) -> Optional['ResourceBase']:
        """Get a single resource from the simulation."""
        return registry.get_module("resource", name)  # type: ignore

    def modules(self, module_type: str) -> Iterator["ModuleBase"]:
        """Gets modules of a given type"""
        return registry.get_modules(module_type)  # type: ignore

    def default(self, name: str, default_object: Any | None = None):
        """Get the default setting from a configuration object. Creates a config object ig it doesn't exist yet."""
        pass

    def __setattr__(self, name: str, value: Any) -> None:

        if isinstance(value, Module):
            self.__modules__[name] = value
            # return
            # log.debug()
        returned = super().__setattr__(name, value)

        return returned

    def __getattribute__(self, __name: str) -> Any:
        # self.__modules__
        # modules = object.__getattribute__(self, "__modules__")
        mods = super().__getattribute__("__modules__")
        # log.debug(__name in mods.keys())
        # log.debug(__name)
        # if __name in modules:
        #     log.error(__name)
        # if __name in object.__getattribute__(self, "__modules__"):
        # return self.__modules__[__name]
        return super().__getattribute__(__name)


def main():

    class ExampleModule(Module):
        hello: str


if __name__ == "__main__":
    main()