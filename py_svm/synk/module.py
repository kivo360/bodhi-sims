# from posixpath import split
# Standard Library
from typing import (Any, Iterable, Set, Dict, Tuple, Callable, ClassVar,
                    Iterator, Optional, cast)

from loguru import logger as log
import pyrsistent
import stringcase

from py_svm.core import registry
from py_svm.utils import get_uuid
from py_svm.synk.abcs.base import isattr
from py_svm.synk.abcs.base import ModuleBase
from py_svm.synk.abcs.base import ResourceBase
from py_svm.synk.abcs.actions import DBActions
from py_svm.synk.abcs.resource import Clock


class Module(ModuleBase, DBActions):

    timestep: int = 0

    @property
    def resources(self) -> Iterable["ResourceBase"]:
        """
        > This function returns a weakref value dictionary of all the resources in the project
        :return: A dictionary of all the resources in the project.
        """
        return list(self.modules_by_type("resource"))  # type: ignore

    @property
    def clock(self) -> Clock:
        return cast(Clock, self.resource("clock"))

    def resource(self, name) -> Optional['ResourceBase']:
        """Get a single resource from the simulation."""
        return registry.get_module("resource", name)  # type: ignore

    def modules_by_type(self, module_type: str) -> Iterator["ModuleBase"]:
        """Gets modules of a given type"""
        return registry.get_modules(module_type)  # type: ignore

    def default(self, name: str, default_object: Any | None = None):
        """Get the default setting from a configuration object. Creates a config object ig it doesn't exist yet."""

    def __setattr__(self, name: str, value: Any) -> None:

        if isinstance(value, Module):
            self.add_module(name, value)
            return

        returned = super().__setattr__(name, value)

        return returned

    def __getattribute__(self, __name: str) -> Any:
        # self.__modules__
        # modules = object.__getattribute__(self, "__modules__")
        # mods = super().__getattribute__("__modules__")
        return super().__getattribute__(__name)

    def __getattr__(self, name: str):
        if name in self.__modules__:
            return self.__modules__[name]

    def add_module(self, name: str, module: 'Module') -> None:
        """
        Add a module type to the module.
        :param name: The name of the module.
        :param module_type: The type of the module.
        """
        if not isinstance(module, Module) and module is not None:
            raise TypeError("{} is not a Module subclass")
        elif isattr(self, name) and name not in self.__modules__:
            raise KeyError("attribute '{}' already exists".format(name))
        elif "." in name:
            raise KeyError(
                'module name can\'t contain ".", got: {}'.format(name))
        elif name == "":
            raise KeyError('module name can\'t be empty string ""')
        self.__modules__[name] = module

    def named_children(self) -> Iterator[Tuple[str, "Module"]]:
        r"""Returns an iterator over immediate children modules, yielding both
        the name of the module as well as the module itself.

        Yields:
            (string, Module): Tuple containing a name and child module

        Example::

            >>> for name, module in model.named_children():
            >>>     if name in ['conv4', 'conv5']:
            >>>         print(module)

        """
        memo = set()
        for name, module in self.__modules__.items():
            if module is not None and module not in memo:
                memo.add(module)
                yield name, module

    def modules(self) -> Iterator["Module"]:
        for _, module in self.named_modules():
            yield module

    def named_modules(
        self,
        memo: Optional[Set["Module"]] = None,
        prefix: str = "",
        remove_duplicate: bool = True,
    ):
        r"""Returns an iterator over all modules in the network, yielding
        both the name of the module as well as the module itself.

        Args:
            memo: a memo to store the set of modules already added to the result
            prefix: a prefix that will be added to the name of the module
            remove_duplicate: whether to remove the duplicated module instances in the result
                or not

        Yields:
            (string, Module): Tuple of name and module

        Note:
            Duplicate modules are returned only once. In the following
            example, ``l`` will be returned only once.

        Example::

            >>> l = nn.Linear(2, 2)
            >>> net = nn.Sequential(l, l)
            >>> for idx, m in enumerate(net.named_modules()):
                    print(idx, '->', m)

            0 -> ('', Sequential(
              (0): Linear(in_features=2, out_features=2, bias=True)
              (1): Linear(in_features=2, out_features=2, bias=True)
            ))
            1 -> ('0', Linear(in_features=2, out_features=2, bias=True))

        """

        if memo is None:
            memo = set()

        if self not in memo:
            if remove_duplicate:
                memo.add(self)
            yield prefix, self
            for name, module in self.__modules__.items():
                if module is None:
                    continue
                submodule_prefix = prefix + ("." if prefix else "") + name
                for m in module.named_modules(memo, submodule_prefix,
                                              remove_duplicate):
                    yield m

    def truename(self, hook: Callable):
        # snake_class = stringcase.snakecase(self.__class__.__name__)
        hook_class = stringcase.snakecase(hook.__name__)
        return f"{hook_class}"

    def register_step_prehook(self, hook: Callable) -> None:
        """
        Register a hook to be called when this module is used in a forward pass.
        """
        self._step_pre_hooks[self.truename(hook)] = hook

    def register_step_hook(self, hook: Callable) -> None:
        """
        Register a hook to be called when this module is used in a forward pass.
        """
        self._step_hooks[self.truename(hook)] = hook

    def __hash__(self) -> int:
        hashed = hash(pyrsistent.freeze(self.dict()))
        return hashed


def main():

    class ExampleModule(Module):
        hello: str


if __name__ == "__main__":
    main()
