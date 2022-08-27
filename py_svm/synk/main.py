import abc
from typing import Any, ClassVar, Optional
import gym
from pydantic import Field
from py_svm.synk.module import Module
from py_svm.utils import get_uuid
from loguru import logger as log
import random
from functools import wraps
from types import FunctionType
import wrapt


@wrapt.decorator
def pass_through(wrapped, instance, args, kwargs):
    return wrapped(*args, **kwargs)


def wrapper(method):

    @wraps(method)
    def wrapped(*args, **kwargs):
        log.warning("Something is here")
        return method(*args, **kwargs)

    return wrapped


class DataModule(Module):
    module_type: str = "data"


class Instrument(DataModule):
    symbol: str
    open: float
    close: float
    high: float
    low: float
    volume: float
    penos: float

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"


class EnvMetaclass(abc.ABCMeta):

    def __new__(cls, name, bases, attrs):
        return super().__new__(cls, name, bases, attrs)


class AgentEnv(gym.Env, Module):
    module_type: str = "env"
    episode_id: str = ''

    def __init__(self) -> None:
        super().__init__()
        init_price = random.uniform(300, 3003)
        self.instrument = Instrument(
            open=init_price * random.normalvariate(1, 0.1),
            close=init_price,
            high=init_price * random.normalvariate(1, 0.1),
            low=init_price * random.normalvariate(1, 0.1),
            volume=init_price * random.normalvariate(1, 0.1) * 10,
            penos=init_price * random.normalvariate(1, 0.1) * 10,
            timestep=3,
            symbol="AAPL")

    def reset(self):
        super().reset()
        self.episode_id = get_uuid()

    def step(self, action: Any):
        # Stop at decorating the step function to inject the timestep and episode_id into the environment
        pass


def run():
    # Create a new Price module
    # Can now run a hook onto the step function.
    # Need to fix the query string. Might do processing of the query string on the python side to prevent turning string into number.
    env = AgentEnv()
    env.reset()
    env.step(None)
    init_price = random.uniform(300, 3003)
    price = Instrument(open=init_price * random.normalvariate(1, 0.1),
                       close=init_price,
                       high=init_price * random.normalvariate(1, 0.1),
                       low=init_price * random.normalvariate(1, 0.1),
                       volume=init_price * random.normalvariate(1, 0.1) * 10,
                       penos=init_price * random.normalvariate(1, 0.1) * 10,
                       timestep=3,
                       symbol="AAPL",
                       episode_id=get_uuid())

    # # price = Price(timestep=0, open=1, close=1, high=1, low=1, volume=1)
    price.episode_id = get_uuid()
    log.success(price.save())
    # log.error(price.latest())
    # # log.info(price.latest_by(2))
    # # log.warning(price.many(1000))
    # # log.debug(price.many_by(2))
    # log.debug(price.count())
    # log.debug(price.find)
    # log.debug(price.find_unique)
    # log.debug(price.delete_one)
    # log.debug(price.delete_many)
    # log.warning(b)
    # Create a single price indicator
    # Get the absolute latest price.
    # Make sure to set the price for a given time.
    # print("hello world")
    # print(price)
    # print(price.processor)


if __name__ == "__main__":
    run()