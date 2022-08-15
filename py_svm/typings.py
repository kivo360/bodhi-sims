from typing import Optional, Sequence, Tuple, TypeVar, Any
import traitlets

Address = TypeVar("Address", str, bytes)
ReprArgs = Sequence[Tuple[Optional[str], Any]]
