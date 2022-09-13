# from py_svm.synk.abc import DatabaseAPI
# Standard Library
import abc
import uuid
from typing import (Any, cast, Dict, List, Union, Callable, Iterator, Optional,
                    MutableMapping)
from pathlib import Path
from itertools import count
from contextvars import Context
from contextvars import ContextVar
from contextvars import copy_context

import anyio
from loguru import logger as log
from devtools import debug
from diskcache import Cache
from eth_utils import ValidationError  # type: ignore
from eth_utils.toolz import nth  # type: ignore
from eth_utils.toolz import first  # type: ignore

from py_svm.typings import JournalDBCheckpoint
from py_svm.synk.models import Metadata


class DeletedEntry:
    pass


# Track two different kinds of deletion:

# 1. key in wrapped
# 2. key modified in journal
# 3. key deleted
DELETE_WRAPPED = DeletedEntry()
get_next_checkpoint = cast(Callable[[], JournalDBCheckpoint], count().__next__)

# 1. key not in wrapped
# 2. key created in journal
# 3. key deleted
REVERT_TO_WRAPPED = DeletedEntry()

ChangesetValue = Union[bytes, DeletedEntry]
ChangesetDict = Dict[bytes, ChangesetValue]


class DatabaseAPI(MutableMapping, abc.ABC):

    def __init__(self):
        pass

    def set(self, key, value, **kwargs):
        raise NotImplementedError("'Set' function not implemented")

    def get(self, key, **kwargs):
        raise NotImplementedError("'Get' function not implemented")

    def delete(self, key, **kwargs):
        raise NotImplementedError("'Delete' function not implemented")

    def exists(self, key, **kwargs) -> bool:
        raise NotImplementedError("'Exist' function not implemented")

    def __contains__(self, key):
        if hasattr(self, "exists"):
            return self.exists(key)
        return super().__contains__(key)

    def __getitem__(self, key):
        if hasattr(self, "get"):
            return self.get(key)
        return super().__getitem__(key)

    def __setitem__(self, key, value) -> None:
        if hasattr(self, "set"):
            return self.set(key, value)
        return super().__setitem__(key, value)

    def __delitem__(self, key) -> None:
        if hasattr(self, "delete"):
            return self.delete(key)
        return super().__delitem__(key)

    def __iter__(self) -> Iterator[Any]:
        return super().__iter__()

    def __len__(self) -> int:
        return super().__len__()

    def use_if_exists(self, name: str, *args, **kwargs):
        if hasattr(self, name):
            return getattr(self, name)(*args, **kwargs)
        return False


# class BaseDB(DatabaseAPI):


class CacheDB(DatabaseAPI):

    def __init__(self):
        self.cache = {}

    def set(self, key, value):
        self.cache[key] = value

    def get(self, key):
        return self.cache.get(key)

    def delete(self, key):
        del self.cache[key]

    def exists(self, key) -> bool:
        return key in self.cache

    def remove(self, key):
        self.delete(key)


class LocalDB(DatabaseAPI):

    def __init__(self):
        self.cache = {}

    def set(self, key, value):
        self.cache[key] = value

    def get(self, key):
        return self.cache.get(key)

    def delete(self, key):
        del self.cache[key]

    def exists(self, key) -> bool:
        return key in self.cache

    def remove(self, key):
        self.delete(key)


class AnalysisDB(DatabaseAPI):

    def __init__(self):
        self.cache = {}

    def set(self, key, value):
        self.cache[key] = value

    def get(self, key):
        return self.cache.get(key)

    def delete(self, key):
        del self.cache[key]

    def exists(self, key) -> bool:
        return key in self.cache

    def remove(self, key):
        self.delete(key)


class StorageLayer(DatabaseAPI):

    def __init__(
            self,
            cache: CacheDB = CacheDB(),
            local: LocalDB = LocalDB(),
            analyze: AnalysisDB = AnalysisDB(),
    ):
        self._cache = cache
        self._local = local
        self._analytics = analyze

    def set_context(self, context: Metadata) -> "StorageLayer":
        self._context = context
        return self

    def set(self, key, value):
        self._cache.set(key, value)
        self._local.set(key, value)
        self._analytics.set(key, value)

    def get(self, key):
        if not self.exists(key):
            raise RuntimeError(f"Couldn't find key {key}")
        if key in self._cache:
            return self._cache.get(key)
        elif key in self._local:
            return self._local.get(key)
        elif key in self._analytics:
            return self._analytics.get(key)

    def remove(self, key):
        if not self.exists(key):
            return False
        self._cache.remove(key)
        self._local.remove(key)
        self._analytics.remove(key)
        return True

    def exists(self, key) -> bool:
        if self._cache.exists(key):
            return True

        if self._local.exists(key):
            return True

        if self._analytics.exists(key):
            return True

        return False


class ContextManager:

    def __init__(self):
        self._ctx_vars: Dict[str, Any] = {}
        self.cxt = Context()

    def copy(self) -> Context:
        return copy_context()

    def flattened(self):
        #  if not isinstance(v, ContextVar)
        return {k.name: v for k, v in self.copy().items()}

    def set(self, key, value):
        self._ctx_vars[key] = ContextVar(key).set(value)

    def get(self, key):
        if key in self._ctx_vars:
            return self._ctx_vars[key].get()
        log.warning("Work damn it!!!")

    def delete(self, key):
        if key in self._ctx_vars:
            self._ctx_vars[key].reset()

    def as_model(self):
        return Metadata(**self.flattened())

    def log_context(self):
        meta = self.as_model()

        debug(meta)


class SearchDB(DatabaseAPI):

    def __init__(self):

        self.cache = {}

    def set(self, key, value):
        self.cache[key] = value

    def get(self, key):
        return self.cache.get(key)

    def delete(self, key):
        del self.cache[key]

    def exists(self, key) -> bool:
        return key in self.cache

    def remove(self, key):
        self.delete(key)


class StorageModel(DatabaseAPI):
    """Works like a journal. We keep track of dictionary changes then commit the changes to the database upon completion of the episode"""

    def __init__(self, eager=False) -> None:

        self.layed_storage = StorageLayer()
        self.search = SearchDB()
        self._current_values = {}
        self._is_eager: bool = eager

    @property
    def ctx(self):
        """The object that manages the current context. This context is used to track the module, episode, parameters, etc."""
        _ctx = copy_context()
        return _ctx

    def set(
        self,
        name: str,
        value: str,
    ) -> None:
        self._current_values[name] = value
        self.eager_commit()

    def get(self, key: str) -> Optional[str]:
        if key in self._current_values:
            return self._current_values[key]
        return self.layed_storage.get(key)

    def exists(self, key: str) -> bool:
        if key in self._current_values:
            return True
        return self.layed_storage.exists(key)

    def delete(self, key, **kwargs):
        return self.layed_storage.delete(key, **kwargs)

    def eager_commit(self):
        """Runs an eager commit if the model eagerly runs."""
        if self._is_eager:
            self.commit()

    def reset(self):
        self._current_values = {}

    def commit(self):
        """Commit values to the database"""
        if len(self._current_values):
            for key, value in self._current_values.items():
                self.layed_storage.set(key, value)


class Experiment:

    def __init__(self, cache_location: str | Path = Path("/tmp/experiment")):
        self.cache_path = Path(cache_location)
        self.cache_path.mkdir(parents=True, exist_ok=True)

        self.cache = Cache(str(self.cache_path))
        self.TRI_STR = "trial_num"
        self.episode_str = "episode"
        self.time_key = "timestep"

    @property
    def trial_count(self) -> int:
        if self.TRI_STR not in self.cache:
            self.cache.set(self.TRI_STR, 0)
        return self.cache.get(self.TRI_STR, 0)

    @property
    def episode(self):
        is_skip = False
        if self.episode_str not in self.cache:
            self.cache[self.episode_str] = str(uuid.uuid4())
            log.error("Episode not found")

            is_skip = True

        if ((self.trial_count % 5) == 0 or
            (self.trial_count == 0)) and not is_skip:
            self.cache[self.episode_str] = str(uuid.uuid4())
        return self.cache[self.episode_str]

    @property
    def timestep(self):
        _key = "timestep"
        if self.time_key not in self.cache:
            self.cache.set(self.time_key, 0)
        return self.cache[self.time_key]

    def incr_trial(self):
        self.cache.set(self.TRI_STR, self.trial_count + 1)

    def step_time(self):
        self.cache.set(self.time_key, self.timestep + 1)

    def __enter__(self):
        self.cache = self.cache.__enter__()
        trial = self.trial_count
        return self

    def __exit__(self, exc_type, exc_value, trace):
        self.incr_trial()
        self.step_time()
        self.episode
        self.cache.close()


class BaseHandler(abc.ABC):

    @abc.abstractmethod
    def check(self) -> bool:
        """Checks that the required context variables are set."""
        raise NotImplementedError

    @abc.abstractmethod
    def save(self, data: dict):
        """Upserts data along side context"""
        raise NotImplementedError

    @abc.abstractmethod
    def latest(self, query: dict = {}):

        raise NotImplementedError

    @abc.abstractmethod
    def latest_by(self, timestep: int = -1, query_dict: dict = {}):
        raise NotImplementedError

    @abc.abstractmethod
    def many(self, limit: int = 100):
        raise NotImplementedError

    @abc.abstractmethod
    def save_many(self, data: List[Dict[str, Any]]):
        raise NotImplementedError

    @abc.abstractmethod
    def count(self, query: Dict[str, Any] = {}) -> int:
        raise NotImplementedError

    def find(self, query: Dict[str, Any] = {}):
        pass

    def find_unique(self, query: Dict[str, Any] = {}):
        pass

    def delete_one(self, query: Dict[str, Any] = {}):
        pass

    def delete_many(self, query: Dict[str, Any] = {}):
        pass


class DatabaseHandler(BaseHandler):

    def __init__(self, processor):
        self._processor = processor
        self._context = ContextManager()

    @property
    def context(self):
        """The context property."""
        return self._context

    @context.setter
    def context(self, value):
        self._context = value

    @property
    def processor(self):
        """The processor property."""
        return self._processor

    @processor.setter
    def processor(self, value):
        self._processor = value

    def between(self, start: int, end: int, query: dict = {}):
        pass

    def count(self) -> int:
        """Given the metadata context, return the number of items in the"""
        return 0

    def latest(self, query: dict = {}):
        return super().latest()

    def latest_by(self, timestep: int = -1, query: dict = {}):
        return super().latest_by(timestep, query)

    def find(self, query: dict = {}):
        pass

    def find_unique(self, query: dict = {}):
        pass

    def save(self, dict: dict):
        pass

    def many(self, query: dict = {}):
        pass

    def many_by(self, timestep: int = -1, query: dict = {}):
        pass


async def main():
    # Standard Library
    import uuid
    from pathlib import Path

    import dataset
    from diskcache import Cache

    ctx_manager = ContextManager()
    ctx_manager.set("episode", "57c9aef7f0636fe6cf482268c6f2c48cab212e9f")
    ctx_manager.set("module_id", uuid.uuid4().hex)
    ctx_manager.set("is_entry", False)
    ctx_manager.set("is_episode", True)
    ctx_manager.set("module_type", "clock")
    ctx_manager.set("module_class", "agent")

    ctx_manager.log_context()

    playpath = Path("/tmp/playcache")
    playpath.mkdir(parents=True, exist_ok=True)
    cache = Cache(playpath)
    db = dataset.connect("sqlite:///mydatabase.db")
    table = db.get_table("state")
    table.create_index([
        "episode",
        "module_type",
        "module_class",
        "timestep",
        "is_episode",
        "module_id",
    ])
    # with cache as session:
    count = cache.get("test_count", 0)

    TEST_MODULE_ID = str(uuid.uuid4())
    experiment = Experiment()
    for _ in range(10):
        log.info(f"Count: {_}")
        with experiment as expr:

            table.insert(
                dict(
                    slot="John Doe",
                    value="49",
                    module_type="China",
                    module_class="agent",
                    episode=expr.episode,
                    module_id=TEST_MODULE_ID,
                    is_episode=True,
                    timestep=expr.timestep,
                ))

    # Get the last
    debug(
        list(
            table.find(
                timestep={">=": 700},
                episode=experiment.episode,
                module_class="agent",
            )))


if __name__ == "__main__":
    anyio.run(main)

# def main():

# if __name__ == "__main__":
#     main()
