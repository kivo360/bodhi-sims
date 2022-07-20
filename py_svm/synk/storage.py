from py_svm.synk.abc import DatabaseAPI


class StorageAPI(DatabaseAPI):
    def set(self, key: bytes, value: bytes) -> None:
        """
        Assign the ``value`` to the ``key``.
        """
        ...

    def exists(self, key: bytes) -> bool:
        """
        Return ``True`` if the ``key`` exists in the database, otherwise ``False``.
        """
        ...

    def delete(self, key: bytes) -> None:
        """
        Delete the given ``key`` from the database.
        """
        ...
