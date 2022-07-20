from __future__ import annotations
from datetime import datetime

from collections import OrderedDict, defaultdict

# mypy
from typing import Dict, Iterator, List, Type, Union


class Clock(object):
    """A class to track the time for a process.

    Attributes
    ----------
    start : int
        The time of start for the clock.
    step : int
        The time of the process the clock is at currently.

    Methods
    -------
    now(format=None)
        Gets the current time in the provided format.
    increment()
        Increments the clock by specified time increment.
    reset()
        Resets the clock.
    """

    def __init__(self):
        self.start = 0
        self.step = self.start

    def now(self, format: str = None) -> datetime:
        """Gets the current time in the provided format.
        Parameters
        ----------
        format : str or None, optional
            The format to put the current time into.

        Returns
        -------
        datetime
            The current time.
        """
        return datetime.now().strftime(format) if format else datetime.now()

    def increment(self) -> None:
        """Increments the clock by specified time increment."""
        self.step += 1

    def reset(self) -> None:
        """Resets the clock."""
        self.step = self.start


# class BaseScheduler:
#     """Simplest scheduler; activates agents one at a time, in the order
#     they were added.

#     Assumes that each agent added has a *step* method which takes no arguments.

#     (This is explicitly meant to replicate the scheduler in MASON).

#     """

#     def __init__(self, model: Model) -> None:
#         """Create a new, empty BaseScheduler."""
#         self.model = model
#         self.steps = 0
#         self.time: TimeT = 0
#         self._agents: Dict[int, Agent] = OrderedDict()

#     def add(self, agent: Agent) -> None:
#         """Add an Agent object to the schedule.

#         Args:
#             agent: An Agent to be added to the schedule. NOTE: The agent must
#             have a step() method.

#         """

#         if agent.unique_id in self._agents:
#             raise Exception(
#                 f"Agent with unique id {repr(agent.unique_id)} already added to scheduler"
#             )

#         self._agents[agent.unique_id] = agent

#     def remove(self, agent: Agent) -> None:
#         """Remove all instances of a given agent from the schedule.

#         Args:
#             agent: An agent object.

#         """
#         del self._agents[agent.unique_id]

#     def step(self) -> None:
#         """Execute the step of all the agents, one at a time."""
#         for agent in self.agent_buffer(shuffled=False):
#             agent.step()
#         self.steps += 1
#         self.time += 1

#     def get_agent_count(self) -> int:
#         """Returns the current number of agents in the queue."""
#         return len(self._agents.keys())

#     @property
#     def agents(self) -> List[Agent]:
#         return list(self._agents.values())

#     def agent_buffer(self, shuffled: bool = False) -> Iterator[Agent]:
#         """Simple generator that yields the agents while letting the user
#         remove and/or add agents during stepping.

#         """
#         agent_keys = list(self._agents.keys())
#         if shuffled:
#             self.model.random.shuffle(agent_keys)

#         for key in agent_keys:
#             if key in self._agents:
#                 yield self._agents[key]


# class RandomActivation(BaseScheduler):
#     """A scheduler which activates each agent once per step, in random order,
#     with the order reshuffled every step.

#     This is equivalent to the NetLogo 'ask agents...' and is generally the
#     default behavior for an ABM.

#     Assumes that all agents have a step(model) method.

#     """

#     def step(self) -> None:
#         """Executes the step of all agents, one at a time, in
#         random order.

#         """
#         for agent in self.agent_buffer(shuffled=True):
#             agent.step()
#         self.steps += 1
#         self.time += 1
