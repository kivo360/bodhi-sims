from collections import UserDict
# Standard Library
from typing import (Any, Dict)
# from py_svm.synk.abc import DatabaseAPI
from contextvars import Context
from contextvars import ContextVar
from contextvars import copy_context

from eth_utils import ValidationError  # type: ignore
from eth_utils.toolz import nth  # type: ignore
from eth_utils.toolz import first
from pydantic import Field  # type: ignore
from pydantic.fields import FieldInfo  # type: ignore

from py_svm.synk.models import Metadata
import devtools as dtoolz
from py_svm.utils import dataclass_transform


class ContextControl:

    def __init__(self):
        self._ctx_vars: Dict[str, Any] = {}
        self.cxt = Context()

    def copy(self) -> Context:
        return copy_context()

    def flattened(self):
        #  if not isinstance(v, ContextVar)
        return {k.name: v for k, v in self.copy().items()}

    def set(self, key, value):
        self._ctx_vars[key] = ContextVar(key).set(value)

    def get(self, key):
        if key in self._ctx_vars:
            return self._ctx_vars[key].get()

    def delete(self, key):
        if key in self._ctx_vars:
            self._ctx_vars[key].reset()

    def as_model(self) -> Metadata:
        return Metadata(**self.flattened())

    def log_context(self):
        meta = self.as_model()

        dtoolz.debug(meta)


class UserContext(UserDict):
    """A context that is injected into every instance of a class that is
    a subclass of `Component`.
    """

    def __init__(self, **kwargs):
        super(UserContext, self).__init__(**kwargs)
        self.__dict__ = {**self.__dict__, **self.data}

    def __str__(self):
        data = [
            "{}={}".format(k, getattr(self, k))
            for k in self.__slots__  # type: ignore
        ]  # type: ignore
        return "<{}: {}>".format(self.__class__.__name__, ", ".join(data))


@dataclass_transform(kw_only_default=True, field_descriptors=(Field, FieldInfo))
class ContextualizedMixin:
    """A mixin that is to be mixed with any class that must function in a
    contextual setting.
    """

    @property
    def context(self) -> ContextControl:
        """Gets the `Context` the object is under.
        Returns
        -------
        `Context`
            The context the object is under.
        """
        return self._context

    @context.setter
    def context(self, context: ContextControl) -> None:
        """Sets the context for the object.
        Parameters
        ----------
        context : `Context`
            The context to set for the object.
        """
        self._context = context
