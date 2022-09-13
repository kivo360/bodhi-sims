__version__ = "0.1.0"
import sys
from pydantic.dataclasses import dataclass
from loguru import logger as log

log.remove()
log.add(
    sys.stderr,
    format=
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <cyan>{file.path}:{line}</cyan> - <level>{message}</level>",
    enqueue=True,
)

__all__ = ["__version__", "dataclass", "log"]
