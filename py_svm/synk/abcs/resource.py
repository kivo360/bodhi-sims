from typing import ClassVar, Tuple

from py_svm.utils import isattr
from .base import ResourceBase
from typing import (Any, Set, cast, Dict, List, Type, Tuple, Union, TypeVar,
                    Callable, ClassVar, Iterator, Optional, MutableMapping)
from pydantic import root_validator
from py_svm.synk.abcs.actions import DBActions

from loguru import logger as log


class Resource(ResourceBase, DBActions):
    module_type: str = "resource"
    pass


class Clock(Resource):
    module_type: str = "resource"
    start: int = 0
    step: int = 0

    @root_validator
    def root_init(cls, values):
        values['step'] = values['start']
        return values

    def increment(self) -> None:
        """Increments the clock by specified time increment."""
        self.step += 1
        self.timestep = self.step
        self.save()

    def reset(self) -> None:
        """Resets the clock."""
        self.check()
        if not self.count():
            # Gonna do compuationally expensive stuff here for now. Will compress into a single operation later.
            self.step = self.start
            log.debug(self.save())
            return
        latest = self.latest()
        if latest.success():
            if not latest.empty():
                record = latest.first()
                self.step = record['start']
                self.step = record['step']
                return
                # return latest.result[0]['step']
            raise ValueError("Non-empty count, yet no latest result.")
