from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Entry(ABC):
    cn: str
    ou: str

    @property
    def dn(self) -> str:
        return f"CN={self.cn},{self.ou}"

    @abstractmethod
    def serialize(self) -> dict: ...
