from email.policy import default
from sqlalchemy import (
    Table,
    table,
    Column,
    column,
    Integer,
    Numeric,
    String,
    MetaData,
    ForeignKey,
    create_engine,
    select,
    func,
    cast,
)

from loguru import logger

# addresses = Table(
#     "addresses",
#     metadata_obj,
#     Column("id", Integer, primary_key=True),
#     Column("user_id", None, ForeignKey("users.id")),
#     Column("email_address", String, nullable=False),
# )


def main():
    from sqlalchemy.dialects.postgresql import insert
    from sqlalchemy.dialects.sqlite import insert as sinsert

    engine = create_engine("sqlite:///:memory:", echo=True)
    metadata_obj = MetaData(bind=engine)
    accounts = Table(
        "accounts",
        metadata_obj,
        Column("id", String, primary_key=True),
        Column("episode", String),
        Column("address", String),
        Column("balance", String),
        Column("timestamp", Integer),
    )
    acc_stmt = sinsert(accounts)
    acc_stmt = acc_stmt.on_conflict_do_update(
        index_elements=[
            accounts.c.episode,
            accounts.c.address,
            accounts.c.timestamp,
        ],
        set_=dict(balance=accounts.c.balance),
    )
    storage = Table(
        "storage",
        metadata_obj,
        Column("id", Integer, primary_key=True),
        Column("episode", String),
        Column("address", String),
        Column("slot", String),
        Column("value", String),
        Column("timestamp", Integer),
    )
    # history = Table(
    #     "history",
    #     metadata_obj,
    #     Column("id", Integer, primary_key=True),
    #     # Column("episode", String, primary_key=True),
    #     # Column("", String, primary_key=True),
    #     Column("timestamp", Integer),
    # )
    metadata_obj.create_all(checkfirst=True)
    # stmt = sinsert(storage)
    # stmt = stmt.on_conflict_do_update(
    #     index_elements=[
    #         storage.c.episode,
    #         storage.c.address,
    #         storage.c.slot,
    #         storage.c.timestamp,
    #     ],
    #     set_=dict(value=storage.c.value),
    # )
    # by_current = select(storage).where(
    #     storage.c.episode == "",
    #     storage.c.address == "",
    # )
    # group_ts = by_current.group_by(storage.c.timestamp)
    # logger.debug(acc_stmt)
    # logger.info(by_current)

    # latest_store = group_ts.order_by(storage.c.timestamp.desc()).limit(1)
    # logger.debug(stmt)
    # logger.warning(latest_store)
    # print("Hello World!")


if __name__ == "__main__":
    main()
