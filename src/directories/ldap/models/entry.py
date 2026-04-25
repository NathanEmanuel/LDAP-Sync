from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar, Type, TypeVar

from ldap3 import Entry as RawEntry

T = TypeVar("T", bound="Entry")


@dataclass
class Entry(ABC):
    cn: str
    ou: str
    object_class: ClassVar[str]

    @property
    def dn(self) -> str:
        return f"CN={self.cn},{self.ou}"

    def get_id(self) -> str:
        return self.cn

    def get_object_class(self) -> str:
        return self.object_class

    @abstractmethod
    def get_name(self) -> str:
        """Not the same as 'name' in AD!"""
        ...

    @abstractmethod
    def serialize_for_creation(self) -> dict: ...

    @classmethod
    @abstractmethod
    def from_raw_entry(cls: Type[T], ou: str, entry: RawEntry) -> T: ...
