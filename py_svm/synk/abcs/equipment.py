"""This file contains the general abstract methods that will be used for all"""

import abc
import uuid
from typing import Any, List, cast
from py_svm.utils import get_uuid
import pyarrow as pa
from pydantic import BaseModel, Field, validator
from py_svm.synk.abcs.base import ModuleBase


class Equipment(BaseModel, abc.ABC):
    name: str | None = None
    episode: uuid.UUID = Field(default_factory=get_uuid)
    source: uuid.UUID | None = None
    target: uuid.UUID | None = None
    timestep: int | None = None


class GenericIO(Equipment, abc.ABC):
    timestep: int = 0
    name: str


class Action(GenericIO, abc.ABC):
    value: Any


class Decision(GenericIO, abc.ABC):
    value: Any


class Metric(GenericIO, abc.ABC):
    value: Any


class Metrics(GenericIO, abc.ABC):
    metrics: List[Metric] = []


class Forward(Equipment, abc.ABC):

    parent: ModuleBase

    @validator('name', pre=True, always=True)
    def validate_name(cls, name, values):
        if name is None:
            return cast(ModuleBase, values['parent']).get_name()
        return name

    def model(self) -> ModuleBase:
        """Returns the parent module."""
        return self.parent

    def state(self) -> BaseModel:
        raise NotImplementedError

    def tensor(self) -> pa.Tensor:
        raise NotImplementedError

    def vector(self) -> pa.Tensor:
        raise NotImplementedError
