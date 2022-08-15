from __future__ import annotations
import abc
from dataclasses import field
from decimal import Decimal
import enum
import random
from loguru import logger

import numpy as np
from py_svm import dataclass, log
from py_svm.synk.clock import Clock
import networkx as nx
import pyarrow as pa
import pandas as pd
import duckdb
from abc import ABC
import uuid
from typing import Any, Iterator, List, Tuple, cast
from py_svm.typings import Address
from py_svm.synk.abc import DatabaseAPI, BaseDB
from pathlib import Path
from pydantic import BaseConfig, BaseSettings, Field, validator
from py_svm.synk.backends import sql as sqlq
from py_svm.core.agent import Agent
import gym
import vaex

DuckDBConn = duckdb.DuckDBPyConnection
# episode, address, balance, timestamp
@dataclass
class StateCtx:
    address: Address  # type: ignore
    episode: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: int = field(default=0)


class DuckSettings(BaseSettings):
    duckdb_path: Path = "./data/duckdb.db"

    @validator("duckdb_path")
    def create_path(cls, v) -> Path:
        v = cast(Path, v)
        v.parent.mkdir(parents=True, exist_ok=True)
        return v

    class Config:
        env_file = ".env"


class StateDB(ABC):
    def __init__(self, db: BaseDB) -> None:
        super().__init__()
        self._db = db
        self._address: Address | None = None
        self._ctx: StateCtx | None = None
        self.reset()

    def reset(self) -> None:
        for query in self.init_queries:
            self._db.run_query(query)

    def _check_ctx(self, check_ctx) -> None:
        if check_ctx and self._ctx is None:
            raise ValueError("Context is not set")

    @abc.abstractproperty
    def init_queries(self) -> List[str]:
        return []

    def set_state_ctx(self, _ctx: StateCtx) -> None:
        self._ctx = _ctx

    def set_value(self, slot: str, value: Any) -> None:
        self._check_ctx(True)
        self._db.run_query(
            sqlq.INSERT_STORAGE,
            (
                self._ctx.episode,
                self._ctx.address,
                slot,
                value,
                value,
                self._ctx.timestamp,
            ),
        )


class LedgerDB(StateDB):
    def __init__(self, db: BaseDB) -> None:
        super().__init__(db)

    @property
    def init_queries(self) -> List[str]:
        return [sqlq.CREATE_ACCOUNT]

    def set_value(self, slot, value: float) -> None:
        self._check_ctx(True)
        self._db.execute(
            sqlq.INSERT_ACCOUNT_STATE.format(
                address=self._ctx.address,
                episode=self._ctx.episode,
                balance=value,
                timestamp=self._ctx.timestamp,
            ),
        )

    def get_value(self, slot: str) -> float:
        self._check_ctx(True)
        arr = (
            self._db.execute(
                sqlq.SELECT_ACCOUNT_ONE.format(
                    address=self._ctx.address,
                    episode=self._ctx.episode,
                    timestamp=self._ctx.timestamp,
                )
            )[slot][0],
        )
        convert = arr[0].as_py() if arr else None

        return convert

    def get_history(self, slot: str) -> pd.DataFrame:
        self._check_ctx(True)
        return self._db.execute(
            sqlq.SELECT_ACCOUNT_HIST.format(
                address=self._ctx.address,
                episode=self._ctx.episode,
                # timestamp=self._ctx.timestamp,
            )
        )


class StorageDB(StateDB):
    def __init__(self, db: BaseDB) -> None:
        super().__init__(db)

    @property
    def init_queries(self) -> List[str]:
        return [sqlq.CREATE_STORAGE]

    def _get_type(self, value: Any):
        match value:
            case str() | bytes():
                return "String"
            case int() | float() | Decimal():
                return "Numeric"
            case bool():
                return "BOOLEAN"
            case dict():
                return "STRUCT"
            case None:
                return "NULL"

    def set_value(self, slot, value: Any) -> None:
        self._check_ctx(True)
        self._db.execute(
            sqlq.INSERT_STORAGE.format(
                address=self._ctx.address,
                episode=self._ctx.episode,
                slot=slot,
                value=value,
                vtype=self._get_type(value),
                timestamp=self._ctx.timestamp,
            ),
        )

    def get_value(self, slot: str) -> float:
        self._check_ctx(True)

        store_arr = (
            self._db.execute(
                sqlq.GET_STORAGE_ONE.format(
                    address=self._ctx.address,
                    episode=self._ctx.episode,
                    timestamp=self._ctx.timestamp,
                )
            ),
        )
        print(store_arr)
        _resp = store_arr[0].as_py() if store_arr else None

        return _resp

    def get_history(self, slot: str) -> pd.DataFrame:
        self._check_ctx(True)
        return self._db.execute(
            sqlq.GET_STORAGE_HISTORY.format(
                address=self._ctx.address,
                episode=self._ctx.episode,
            )
        )

    def __setattr__(self, slot: str, _value: Any) -> None:
        return super().__setattr__(slot, _value)


class DuckDB(BaseDB):
    def __init__(self, settings: DuckSettings) -> None:
        super().__init__()
        self._settings = settings
        self.conn: DuckDBConn = duckdb.connect(str(self._settings.duckdb_path))

    def connect_db(self, path_str: str) -> DuckDBConn:
        return duckdb.connect(path_str)

    def run_query(self, query: str) -> pa.Table:
        return self.conn.execute(query).fetch_arrow_table()

    def execute(
        self,
        query: str,
        parameters: object = [],
        multiple_parameter_sets: bool = False,
        *args,
        **kwargs,
    ) -> pa.Table:
        return self.conn.execute(
            query,
            parameters=parameters,
            multiple_parameter_sets=multiple_parameter_sets,
        ).fetch_arrow_table()

    def __setstate__(self, d) -> None:
        settings = d.get("settings", {})
        self.conn = self.connect_db(settings.get("duckdb_path", ""))
        # return {"settings": d}

    def __getstate__(self) -> dict:
        _sdict = self._settings.dict()
        _sdict.update({"duckdb_path": str(self._settings.duckdb_path)})
        return {"settings": _sdict}


class MockStateDB(ABC):
    pass


class Config(BaseConfig):
    arbitrary_types_allowed = True


@dataclass(config=Config)
class Storage:
    db: BaseDB
    store: StorageDB | None = None
    ledger: LedgerDB | None = None

    tx_addr: StateCtx | None = None

    def __post_init__(self) -> None:
        if self.store is None or self.ledger is None:
            self.store = StorageDB(self.db)
            self.ledger = LedgerDB(self.db)

    def __setattr__(self, __name: str, __value: Any) -> None:
        super().__setattr__(__name, __value)

    def __getattr__(self, __name: str) -> Any:
        return super().__getattr__(__name)

    def _update_sim_cxt(self, state_ctx: StateCtx) -> None:
        self.tx_addr = state_ctx
        self.store.set_state_ctx(state_ctx)
        self.ledger.set_state_ctx(state_ctx)

    def __getitem__(self, key: str) -> Any:
        match key:
            case "balance":
                return self.ledger.get_value(key)
            case _:
                return self.store.get_value(key)
        # return self.conn.get_value(key)

    def __setitem__(self, slot: str, value: Any) -> None:
        match slot:
            case "balance":
                self.ledger.set_value(slot, value)
            case _:
                self.store.set_value(slot, value)
        # self.ledger.set_value(slot, value)

    def __delitem__(self, key: bytes) -> None:
        self.conn.remove_value(key)

    def __iter__(self) -> Iterator[bytes]:
        return self.conn.iter_values()

    def __len__(self) -> int:
        return self.conn.count_values()

    def _exists(self, key: bytes) -> bool:
        return self.conn.exists(key)

    class Config:
        arbitrary_types_allowed = True


@dataclass
class Account:
    address: Address
    balance: float
    nonce: int = 0
    storage: Storage | None = None
    _balance: str = field(init=False, repr=False, default=100)

    def __post_init__(self) -> None:
        self._reset_storage()

        self.storage.ledger.set_value("balance", 100)

    def _reset_storage(self):
        if self.storage is None:
            self.storage = Storage(db=DuckDB(DuckSettings()))
            self.storage._update_sim_cxt(StateCtx(address=self.address))

    @property
    def balance(self) -> float:
        accessed = self.storage["balance"]
        if accessed:
            self._balance = float(accessed)

        return self._balance

    @balance.setter
    def balance(self, value: float) -> None:
        self._reset_storage()
        if type(value) is property:
            # initial value not specified, use default
            value = Account._balance
        self._balance = value
        self.storage["balance"] = value

    class Config:
        arbitrary_types_allowed = True


def get_hex(max_len: int) -> str:
    return uuid.uuid4().hex[:max_len]


@dataclass
class MockAgent(Agent):
    unique_id: str = field(default_factory=lambda: get_hex(22))
    account: Account = Account("0x123456789012345678901234", 100.0, 0)

    # Testing for the state of the agent
    tts: int = 0

    def __post_init__(self):
        self.test_calls()
        self.test_calls()
        self.test_calls()
        log.info(vaex.from_arrow_table(self.storage.store.get_history("blueboy")))

    def test_calls(self):
        # self.unique_id: str = str(uuid.uuid4().hex)
        self.storage.store.set_value("blueboy", (random.uniform(300, 500) + 100.0))
        df = vaex.from_arrow_table(self.storage.store.get_value("blueboy"))
        log.info(df)
        self.tts += 1

    @property
    def storage(self) -> Storage:
        state_ctx = self.get_state_context()
        self.account.storage._update_sim_cxt(state_ctx)
        return self.account.storage

    def get_state_context(self) -> StateCtx:
        return StateCtx(
            episode=self.unique_id, address=self.account.address, timestamp=self.tts
        )

    def change_eth(self, amount: float):
        self.account.balance += amount


class AgentGym(gym.Env, ABC):

    agent_id: str = None
    episode_id: str = None

    def __init__(self) -> None:
        super().__init__()
        self.clock = Clock()
        self.agent = MockAgent()

        log.warning(self.agent.unique_id)

    def __setattr__(self, __name: str, __value: Any) -> None:
        return super().__setattr__(__name, __value)

    def step(self, action: Any) -> "Tuple[np.array, float, bool, dict]":
        return np.array([]), 0, False, {}

    def reset(self) -> Any:
        return super().reset()

    def render(self, **kwargs) -> None:
        self.clock.reset()


class Outcome(enum.Enum):
    WIN = 1
    LOSE = 2
    DRAW = 3


class Contract:
    def __init__(self) -> None:
        self.account = Account("0x123456789012345678901234", 100.0, 0)
        self.storage["principle"] = 100.0
        self.storage["coupon"] = 10.0
        logger.success(type(self.storage["coupon"]))
        self.end = 0.0

    @property
    def history(self):
        print(
            vaex.from_arrow_table(self.account.storage.store.get_history("principle"))
        )

    @property
    def storage(self) -> Storage:
        return self.account.storage


def main():
    print("")
    cont = Contract()
    cont.history
    clock = Clock()
    clock.reset()
    clock.increment()
    print(clock.step)

    """
    __setattr__
    (contract.principle)
    """

    # AgentGym()
    # ctx = StateCtx(
    # #     episode=uuid.uuid4().hex, address="0x123456789012345678901234", timestamp=0
    # # )
    # account = Account("0x123456789012345678901234", 100.0, 0)
    # print(account.storage.store.get_history("blueboy"))
    # logger.success(account.storage["balance"])
    # # account.storage._update_sim_cxt(ctx)
    # logger.info(account.balance)
    # log.debug(account)
    # import pandas as pd
    # import pyarrow as pa
    # import sys
    # from py_svm.synk.backends import sql
    # from loguru import logger
    # from mimesis.enums import Gender
    # from mimesis.locales import Locale
    # from mimesis.schema import Field, Schema
    # import time

    # logger.remove()
    # logger.add(
    #     sys.stderr,
    #     format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <cyan>{file.path}:{line}</cyan> - <level>{message}</level>",
    #     enqueue=True,
    # )
    # # logger.add(
    # #     sys.stderr,
    # #     format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | <cyan>{file.path}:{line}</cyan> - <level>{message}</level>",
    # #     level="INFO",
    # #     enqueue=True,
    # # )

    # con = duckdb.connect()
    # con.execute(sql.CREATE_ACCOUNT)
    # con.execute(sql.CREATE_STORAGE)

    # _ = Field(locale=Locale.EN)
    # schema = Schema(
    #     schema=lambda: {
    #         # "pk": _("increment"),
    #         "episode": _("token_hex"),
    #         "address": _("ethereum_address"),
    #         # "name": _("text.word"),
    #         # username(mask='l_l_d', drange=(1900, 2021))
    #         "slot": _(
    #             "choice",
    #             items=[
    #                 "bloomberg",
    #                 "withdrawal",
    #                 "deck",
    #                 "sie",
    #                 "combinations",
    #                 "bird",
    #                 "ghost",
    #                 "cameron",
    #                 "keys",
    #                 "lucy",
    #             ],
    #         ),
    #         "value": _(
    #             "choice", items=[_("text.word"), _("integer_number"), _("float_number")]
    #         ),
    #         "timestamp": _("increment"),
    #         "value_choice": {
    #             "word": _("text.word"),
    #             "address": _("ethereum_address"),
    #             "ints": _("integer_number"),
    #             "float": _("float_number"),
    #             "bool": _("boolean"),
    #         },
    #     }
    # )
    # # print("hello")
    # _episode = uuid.uuid4().hex
    # _address = f"0x{uuid.uuid4().hex[10:]}"
    # _ts = 0
    # vals = dict(episode=_episode, address=_address, balance=1001.0, timestamp=_ts)
    # con.execute(
    #     sql.INSERT_ACCOUNT_STATE,
    #     [_episode, _address, 1000000.1, 0],
    # )
    # resp = con.execute(
    #     sql.GET_FIRST_ACCOUNT.format(**vals),
    # ).fetchone()
    # print(resp)
    # con.execute("select * from accounts")
    # logger.debug(con.df())

    # # generated = schema.create(iterations=10)

    # # debug(generated)
    # # logger.debug(rcf)
    # # print(rcf["slot"].to_list())

    # # for obj in schema.loop():
    # #     slot = obj.get("slot")

    # #     logger.info(obj)
    # #     time.sleep(0.1)

    # # con.execute(
    # #     """create table accounts (id int64, episode string, address string, balance DOUBLE, timestamp int64)"""
    # # )
    # # con.execute(
    # #     "insert into accounts (id, episode, address, balance, timestamp) values (1, '233458601e609ab1c330d563326c07fd3dcb8edc', '0x3788f04a76f3c3e6ac5bae908c425ca913111494', 26, 51);"
    # # )
    # # # con.execute(
    # # #     "CREATE TABLE accounts (id INT64, episode STRING, address STRING, balance FLOAT64, timestamp INT64)"
    # # # )
    # # con.execute("select * from accounts")
    # # print(con.df())

    # # rel = duckdb.from_arrow(con.arrow())
    # # print(
    # #     con.values([uuid.uuid4().hex, uuid.uuid4().hex, 100.0, 0]).insert_into(
    # #         "accounts"
    # #     )
    # # )
    # # print(rel)

    # # con.table("accounts")
    # # arrow_table = pa.Table.from_pydict(
    # #     {"address": [1, 2, 3, 4], "j": ["one", "two", "three", "four"]}
    # # )
    # # my_dictionary = {}
    # # my_dictionary["accounts"] = pd.DataFrame.from_dict(
    # #     {"i": [1, 2, 3, 4], "j": ["one", "two", "three", "four"]}
    # # )
    # # con.register("test_df_view", my_dictionary["test_df"])
    # # con.execute("SELECT * FROM test_df_view")
    # # print(con.fetchall())

    # # address = uuid.uuid4().hex[10:]
    # # account = Account(address, 100)
    # # fed = FederatedStorage()
    # # fed.add_account(account)
    # # logger.info(fed.get_account(address))

    # bank account => bank (multiple users) -> user (has bank account) --- (buying things from) --> grocery store

    # Eventually: Data science!!!

    # class BankAccount:
    #     def __init__(self, balance):
    #         self.balance = balance

    #     # open - account
    #     # close - account

    #     def deposit(self, amount):
    #         return

    #     def withdraw(self, amount):
    #         return

    #     def check_balance(self):
    #         return

    #     def is_overdrawn(self):
    #         return
    print("")


if __name__ == "__main__":
    main()
