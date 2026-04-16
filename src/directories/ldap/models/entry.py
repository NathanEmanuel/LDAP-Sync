from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Entry(ABC):
    cn: str
    ou: str

    @property
    def dn(self) -> str:
        return f"CN={self.cn},{self.ou}"

    def get_id(self) -> str:
        return self.cn

    @abstractmethod
    def get_name(self) -> str:
        """Not the same as 'name' in AD!"""
        ...

    @abstractmethod
    def serialize_for_creation(self) -> dict: ...
