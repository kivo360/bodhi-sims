# Standard Library
import abc
import random
import random as rand
import time
import numpy as np
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

    # __grouping__
    class Grouping:
        """ Here we add in a list of elements that will be used to group the data. This can be done either by a Field attribute, or through this class attributes. """
        pass


class Instrument(DataModule):
    # How groups can be defined.
    # symbol: str = Field(..., description="The symbol of the instrument.", example="AAPL", max_length=10, is_group=True)
    symbol: str
    open: float
    close: float
    high: float
    low: float
    volume: float

    class Config:
        arbitrary_types_allowed: bool = True
        extra: str = "allow"

    def reset(self):
        # Why
        print("Resetting instrument")
        pass

    def by_group(self):
        # Should add a cache of a group
        # Just realizing I could try creating queries within pandas as well.
        self._group = self.latest_by(alter={"group_by": "symbol"})


def add_episode(instance: Module, action: Action, *args, **kwds) -> Any:
    """Add an episode to all modules and resources."""
    action_episode = str(action.episode)
    instance.episode = action_episode
    for module in instance.modules():
        module.episode = action_episode
        module.timestep = action.timestep

    # Now add the episode into the resources.
    for resource in instance.resources:
        resource.episode = action_episode
        resource.timestep = action.timestep
        resource.refresh()

    return action


class AgentEnvAbstract(gym.Env, Module, abc.ABC):
    module_type: str = "env"

    def __pre_init__(self, *args, **kwds):
        # log.info("Initializing environment")
        self.register_init_hooks()

    def register_init_hooks(self) -> None:
        """Initialize hooks that you'd want registered for everything."""
        self.register_step_prehook(add_episode)

    def reset(self):
        super().reset()
        if not self.episode:
            self.episode = get_uuid()


class AgentEnv(AgentEnvAbstract):
    module_type: str = "env"

    def __init__(self) -> None:
        super().__init__()
        init_price = rand.uniform(300, 3003)
        self.instrument = Instrument(
            open=init_price * rand.normalvariate(1, 0.1),
            close=init_price,
            high=init_price * rand.normalvariate(1, 0.1),
            low=init_price * rand.normalvariate(1, 0.1),
            volume=init_price * rand.normalvariate(1, 0.1) * 10,
            timestep=3,
            symbol="AAPL")

    def get_state(self):
        return {"state": [], "agents": []}

    def spawn_agent(self):
        """ Get the current state of the environment and spawn an agent with the specifications. """
        # There should be an accessible state from an environment variable.
        states = self.get_state()
        states["agents"].append({"name": "agent", "agent_id:": get_uuid()})
        return states

    def reset(self):
        super().reset()
        self.spawn_agent()
        self.instrument.reset()

    def step(self, action: Action, *args) -> Tuple[Metrics, Decision, bool]:
        # Decorate the step function
        # I wonder if there's anything that allows me to grab all non-resource elements instantly and step through them.
        # Ideally this would be a differential dataflow. It would automatically update variables on input change.
        # After I figure out the structure of the code, I'll consider this as an upgrade. It would dramatically cut down processing time.
        #   We're talking about a 1000x speedup at this position.
        #   A better first start would be to replace the engine in the background with something that includes near cache from Hazelcast.

        log.opt(depth=2).debug(self.clock.step)

        self.clock.walk()

        return Metrics(name="metrics",
                       metrics=[{
                           "name": "accuracy",
                           "value": 0.5
                       }]), Decision(  # type: ignore
                           name="decision",
                           value=random.uniform(0, 1)), False


def run_clock(episode: str) -> dict[str, Clock]:
    clock: 'Clock' = Clock()
    return {'clock': clock}


def activate_env(episode):
    env = AgentEnv()
    example_action = Action(name="action",
                            value=0.5,
                            timestep=1,
                            episode=episode)
    env.reset()
    env.step(example_action)
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
    distro = np.random.beta(81, 219, 1000)

    samples = (distro * 219)
    print("Mean: ", samples.mean())
    print("St. Dev.: ", samples.std())
    print("Variance: ", samples.var())
    print("Median: ", np.median(samples))
    # np.mean(distro)
    # print()
    # from diskcache import Cache
    # # Figure out how to index keys using this style
    # env_cache = Cache('/tmp/env_cache')

    # warnings.simplefilter("ignore")
    # if not 'env_test' in env_cache:
    #     env_cache['env_test'] = get_uuid()
    # random_episode = str(env_cache['env_test'])

    # devtools.debug(random_episode)
    # # Forced to place resources in the main scope to avoid losing the reference.
    # run_clock(random_episode)

    # env = activate_env(random_episode)
    # for i in range(100):
    #     env.step(
    #         Action(name="action", value=0.5, timestep=i,
    #                episode=random_episode))


if __name__ == "__main__":
    run()
