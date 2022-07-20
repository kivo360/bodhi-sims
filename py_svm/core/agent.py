from abc import ABCMeta
from collections import OrderedDict, defaultdict

# mypy
from typing import Dict, Iterator, List, Type, Union, Any
import random
import uuid

from pyparsing import Optional

from py_svm.core.base import TimeIndexed, TimedIdentifiable

TimeT = Union[float, int]


class Agent(TimeIndexed):
    def __init__(self) -> None:
        """Create a new agent.

        Args:
            unique_id (int): A unique numeric identified for the agent
            model: (Model): Instance of the model that contains the agent
        """
        # self.model = model
        self.unique_id: str = str(uuid.uuid4())

    def step(self) -> None:
        """A single step of the agent."""
        pass

    def reset(self) -> None:
        raise NotImplementedError("Agent.reset() is not implemented.")

    def advance(self) -> None:
        pass

    @property
    def random(self) -> random.Random:
        return self.model.random
