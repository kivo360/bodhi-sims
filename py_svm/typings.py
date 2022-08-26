from typing import (
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Any,
    NewType,
    TypedDict,
    Dict,
)

Address = TypeVar("Address", str, bytes)
ReprArgs = Sequence[Tuple[Optional[str], Any]]

JournalDBCheckpoint = NewType("JournalDBCheckpoint", int)

AccountDetails = TypedDict(
    "AccountDetails",
    {
        "balance": int,
        "nonce": int,
        "code": bytes,
        "storage": Dict[int, int]
    },
)
AccountState = Dict[Address, AccountDetails]
DictAny = Dict[str, Any]