from typing import ClassVar, Optional
from ..module import Module
from py_svm.utils import get_uuid


class Behavior(Module):
    module_type: ClassVar[str] = "behavior"

    @property
    def behavior_id(self):
        return get_uuid()
