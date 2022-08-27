# Standard Library
import abc
import random
from typing import Any, Tuple
import warnings

import gym
from loguru import logger as log

from py_svm.utils import get_uuid
from py_svm.synk.module import Module
from py_svm.synk.abcs.equipment import Action
from py_svm.synk.abcs.equipment import Metrics
from py_svm.synk.abcs.equipment import Decision
# from torch.nn.modules.module


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
    episode: str = ''

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
        self.episode = get_uuid()

    def step(self, action: Action, *args) -> Tuple[Metrics, Decision, bool]:
        # Stop at decorating the step function to inject the timestep and episode_id into the environment
        return Metrics(name="metrics",
                       metrics=[{
                           "name": "accuracy",
                           "value": 0.5
                       }]), Decision(  # type: ignore
                           name="decision",
                           value=random.uniform(0, 1)), False

    # def __getattr__(self, name):
    #     log.critical("{} is not a valid attribute of {}".format(
    #         name, self.__class__.__name__))
    #     super().__getattr__(name)


def add_episode(instance: Module, action: Action, *args, **kwds) -> Any:
    instance.episode = str(action.episode)
    for module in instance.modules():
        module.episode = str(action.episode)
    return action


def run():
    warnings.simplefilter("ignore")
    # with warnings.catch_warnings():

    # Create a new Price module
    # Can now run a hook onto the step function.
    # Need to fix the query string. Might do processing of the query string on the python side to prevent turning string into number.
    env = AgentEnv()
    env.register_step_prehook(add_episode)
    env.reset()
    env.step(Action(name="action", value=0.5, timestep=3))
    test_set = set()
    init_price = random.uniform(300, 3003)
    price = Instrument(open=init_price * random.normalvariate(1, 0.1),
                       close=init_price,
                       high=init_price * random.normalvariate(1, 0.1),
                       low=init_price * random.normalvariate(1, 0.1),
                       volume=init_price * random.normalvariate(1, 0.1) * 10,
                       penos=init_price * random.normalvariate(1, 0.1) * 10,
                       timestep=3,
                       symbol="AAPL")

    # if price in test_set:
    #     print("HELLO")
    # # # price = Price(timestep=0, open=1, close=1, high=1, low=1, volume=1)
    # price.episode = get_uuid()
    # log.success(price.save())
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
