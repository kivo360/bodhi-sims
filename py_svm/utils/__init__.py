# Standard Library
import uuid

from loguru import logger as log

from .decorators import dataclass_transform
from .refs import isattr


def get_uuid() -> str:
    return str(uuid.uuid4())
