from typing import ClassVar
from .base import ResourceBase


class Resource(ResourceBase):
    module_type: ClassVar[str] = "resource"
