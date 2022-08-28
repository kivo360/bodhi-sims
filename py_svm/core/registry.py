"""This module hold the project level registry and provides methods to mutate
and change the registry.

"""

import weakref

import stringcase
from py_svm.synk.abc import Module
from py_svm.utils import isattr


class ModuleRegistry:

    def __init__(self) -> None:
        self.__registry = {}
        self.__module_holder = {}

    def create_registry_if_not_exists(self, type_name: str) -> None:
        if type_name not in self.__registry:
            self.__registry[type_name] = weakref.WeakValueDictionary()

    def create_holder_if_not_exists(self, type_name: str) -> None:
        if type_name not in self.__module_holder:
            self.__module_holder[type_name] = dict()

    def add_holder(self, type_name: str, module_name: str,
                   module: "Module") -> None:
        self.create_holder_if_not_exists(type_name)
        self.__module_holder[type_name][module_name] = module

    def add_reference(self, type_name: str, module_name: str,
                      module: "Module") -> None:
        self.register(module, type_name)
        self.add_holder(type_name, module_name, module)

    def get_holder(self, type_name: str, module_name: str) -> dict:
        self.create_holder_if_not_exists(type_name)
        return self.__module_holder[type_name].get(module_name, None)

    def register(self, module: "Module", type_name: str) -> None:
        self.create_registry_if_not_exists(type_name)
        module_name = stringcase.snakecase(module.__class__.__name__)
        self.add_holder(type_name, module_name, module)
        registry_ref = self.__registry[type_name]
        if module_name not in registry_ref:
            # print(weakref.ref(module))
            self.__registry[type_name][module_name] = self.get_holder(
                type_name, module_name)

    def get_type(self, type_name: str) -> weakref.WeakValueDictionary:
        if type_name in self.__registry:
            return self.__registry[type_name]
        self.__registry[type_name] = weakref.WeakValueDictionary()
        return self.__registry[type_name]

    def get_module(self, type_name: str, module_name: str) -> "Module":
        return self.get_type(type_name)[module_name]


_MOD_REGISTRY = ModuleRegistry()


def registry() -> ModuleRegistry:
    """Gets the project level registry.

    Returns
    -------
    dict
        The project level registry.
    """
    return _MOD_REGISTRY


def register(module: "Module", module_type: str) -> None:
    """Registers a component into the registry

    Parameters
    ----------
    component : 'Component'
        The component to be registered.
    registered_name : str
        The name to be associated with the registered component.
    """
    global _MOD_REGISTRY
    _MOD_REGISTRY.register(module, module_type)


def get_module(module_type: str, module_name: str) -> "Module":
    """Gets a module from the registry.

    Parameters
    ----------
    registered_name : str
        The name of the registered component.
    """
    global _MOD_REGISTRY
    return _MOD_REGISTRY.get_module(module_type, module_name)


def get_modules(module_type: str):  # type: ignore
    """Gets a module from the registry.

    Parameters
    ----------
    registered_name : str
        The name of the registered component.
    """
    global _MOD_REGISTRY
    return _MOD_REGISTRY.get_type(module_type).values()

    # print(val)
    # return _MOD_REGISTRY.get_type(module_type)

    # yield name, module
