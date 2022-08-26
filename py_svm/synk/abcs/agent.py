from typing import ClassVar, Optional
from ..module import Module
from py_svm.utils import get_uuid


class Entity(Module):
    module_type: ClassVar[str] = "entity"

    @property
    def entity_id(self):
        """The foo property."""
        return get_uuid()


class Agent(Entity):
    module_type: ClassVar[str] = "agent"

    @property
    def agent_id(self):
        return super().entity_id