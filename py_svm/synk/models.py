from typing import Optional
from py_svm import dataclass
from pydantic import BaseConfig, Extra, ValidationError, validator
from prisma.partials import MetadataWithoutRelations

# base_config = BaseConfig()


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


class Metadata(MetadataWithoutRelations):
    id: Optional[str] = None

    @validator("episode", pre=True, always=True)
    def validate_episode(cls, value, values):
        if "is_episode" in values and values["is_episode"]:
            if not value:
                raise ValidationError(
                    "episode is required for episodic modules", model=type(self)
                )
        return value


def main():
    pass


if __name__ == "__main__":
    main()
