# Standard Library
import abc
import random
import time
from turtle import forward
from typing import Any, Tuple
import warnings

import gym
from loguru import logger as log
from py_svm.core import registry
from py_svm.synk.abcs.resource import Clock

from py_svm.utils import get_uuid
from py_svm.synk.module import Module
from py_svm.synk.abcs.equipment import Action
from py_svm.synk.abcs.equipment import Metrics
from py_svm.synk.abcs.equipment import Decision
# from torch.nn.modules.module
import devtools
import pyroscope

pyroscope.configure(
    application_name="py_svm",  # replace this with some name for your application
    server_address=
    "http://0.0.0.0:4040",  # replace this with the address of your pyroscope server
)


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

    def reset(self):
        devtools.debug(self.resources)


def add_episode(instance: Module, action: Action, *args, **kwds) -> Any:
    instance.episode = str(action.episode)
    for module in instance.modules():
        module.episode = str(action.episode)
        module.timestep = action.timestep

    # Now add the episode into the resources.
    for resource in instance.resources:
        resource.episode = str(action.episode)
        resource.timestep = action.timestep

    return action


class AgentEnvAbstract(gym.Env, Module, abc.ABC):
    module_type: str = "env"

    def register_init_hooks(self) -> None:
        self.register_step_prehook(add_episode)

    def reset(self):
        super().reset()
        self.episode = get_uuid()


class AgentEnv(AgentEnvAbstract):
    module_type: str = "env"

    def __pre_init__(self, *args, **kwds):
        # log.warning(
        #     "AgentEnvAbstract is an abstract class. Use a concrete class instead."
        # )
        self.register_init_hooks()

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
        self.instrument.reset()

    def step(self, action: Action, *args) -> Tuple[Metrics, Decision, bool]:
        # Decorate the step function
        devtools.debug("self.resource('clock')")

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


def run_clock(episode: str):
    clock = Clock()
    clock.episode = episode
    # Network calls are really slow. Will need to optimize this using async and threading.
    with pyroscope.tag_wrapper({"db_call": "increment_clock_step"}):
        clock.reset()
        clock.increment()

    # clock.reset()
    # time.sleep(2)
    # initialize a time (for an episode)
    # search for the step of that time (given an episode)
    # devtools.debug(registry.get_modules('resource'))
    # clock.refresh()
    return {'clock': clock}


def activate_env():
    env = AgentEnv()
    env.reset()
    env.step(Action(name="action", value=0.5, timestep=1))
    # env.register_step_hook(add_episode)
    return env


def db_calls():
    # f27031e2-efb2-4109-9be8-7062f48ad79b
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

    if price in test_set:
        print("HELLO")
    # # price = Price(timestep=0, open=1, close=1, high=1, low=1, volume=1)
    price.episode = get_uuid()
    log.success(price.save())
    log.error(price.latest())
    # log.info(price.latest_by(2))
    # log.warning(price.many(1000))
    # log.debug(price.many_by(2))
    # log.debug(price.count())
    # log.debug(price.find)
    # log.debug(price.find_unique)
    # log.debug(price.delete_one)
    # log.debug(price.delete_many)
    return {"price": price}
    # log.warning(b)


def run():
    from diskcache import Cache

    env_cache = Cache('/tmp/env_cache')

    warnings.simplefilter("ignore")
    if not 'env_test' in env_cache:
        env_cache['env_test'] = get_uuid()
    random_episode = str(env_cache['env_test'])
    # Forced to place resources in the main scope to avoid losing the reference.
    resources = run_clock(random_episode)

    env = activate_env()
    # dbs = db_calls()
    # env = AgentEnv()
    # env.register_step_prehook(add_episode)
    # env.reset()
    # env.step(Action(name="action", value=0.5, timestep=1))
    # test_set = set()
    # init_price = random.uniform(300, 3003)
    # price = Instrument(open=init_price * random.normalvariate(1, 0.1),
    #                    close=init_price,
    #                    high=init_price * random.normalvariate(1, 0.1),
    #                    low=init_price * random.normalvariate(1, 0.1),
    #                    volume=init_price * random.normalvariate(1, 0.1) * 10,
    #                    penos=init_price * random.normalvariate(1, 0.1) * 10,
    #                    timestep=3,
    #                    symbol="AAPL")

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
