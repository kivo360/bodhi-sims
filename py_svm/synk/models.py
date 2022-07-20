from py_svm import dataclass


@dataclass
class Account:
    address: str
    storage: "StorageAPI"


@dataclass
class Contract:
    """
    A representation of a smart contract.
    """

    account: Account


def main():
    pass


if __name__ == "__main__":
    main()
