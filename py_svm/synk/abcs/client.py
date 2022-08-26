import abc
from pydantic import BaseModel
from prisma.client import Prisma

from py_svm.synk.abcs.engine import AbstractEngine


class ClientAbstract(abc.ABC):

    def __init__(self, engine: AbstractEngine, **kwargs):
        self._engine = engine


def main():
    pass


if __name__ == "__main__":
    main()