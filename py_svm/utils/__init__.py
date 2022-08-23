# Standard Library
import uuid

from loguru import logger as log

from .decorators import dataclass_transform


def get_uuid() -> str:
    return str(uuid.uuid4())
