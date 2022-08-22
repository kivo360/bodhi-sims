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
    pass


if __name__ == "__main__":
    main()
