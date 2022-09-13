def isattr(obj: object, name: str) -> bool:
    return bool(getattr(obj, name, None))