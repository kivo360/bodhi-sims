from functools import cached_property
from typing import Optional
from py_svm.synk.module import Module
from py_svm.synk.abcs.engine import AbstractEngine, SurrealEngine
from loguru import logger as log
from py_svm.typings import DictAny
import random


class Price(Module):
    module_type = "price"
    open: float
    close: float
    high: float
    low: float
    volume: float
    penos: float

    # def derp(self):
    #     pass

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"


def run():
    # Create a new Price module
    init_price = random.uniform(300, 3003)
    price = Price(timestep=2,
                  open=init_price * random.normalvariate(1, 0.1),
                  close=init_price,
                  high=init_price * random.normalvariate(1, 0.1),
                  low=init_price * random.normalvariate(1, 0.1),
                  volume=init_price * random.normalvariate(1, 0.1) * 10,
                  penos=init_price * random.normalvariate(1, 0.1) * 10)

    # price = Price(timestep=0, open=1, close=1, high=1, low=1, volume=1)

    price.save()
    log.success(price.engine)
    # Create a single price indicator
    # Get the absolute latest price.
    # Make sure to set the price for a given time.
    # print("hello world")
    # print(price)
    # print(price.processor)


if __name__ == "__main__":
    run()