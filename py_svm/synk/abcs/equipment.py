"""This file contains the general abstract methods that will be used for all"""

import abc
import uuid
from typing import Any, List
from py_svm.utils import get_uuid

from pydantic import BaseModel, Field


class ActionAbstract(BaseModel, abc.ABC):
    episode_id: str = Field(default_factory=get_uuid)
    timestep: int
    value: Any


class DecisionAbstract(BaseModel, abc.ABC):
    episode_id: str = Field(default_factory=get_uuid)
    module_id: uuid.UUID
    value: Any


class Metric(BaseModel):
    name: str
    value: Any


class Metrics(BaseModel, abc.ABC):
    episode_id: str = Field(default_factory=get_uuid)
    metrics: List[Metric] = []
