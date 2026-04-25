from __future__ import annotations

import secrets
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import ClassVar, Optional, Type, TypeVar

from ldap3 import Entry as RawEntry

from directories.active_directory.enums import GroupType, UserAccountControl
from sync.types import DestinationClient, DestinationGroup, DestinationModel, DestinationUser

ENTRY_TYPE = TypeVar("ENTRY_TYPE", bound="Entry")


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
    def from_raw_entry(cls: Type[ENTRY_TYPE], ou: str, entry: RawEntry) -> ENTRY_TYPE: ...





@dataclass
class Group(Entry, DestinationGroup):

    object_class: ClassVar[str] = "group"
    name: str
    description: Optional[str]

    @property
    def account_name(self) -> str:
        return self.name.replace("/", "-")

    def get_name(self) -> str:
        return self.name

    def serialize_for_creation(self) -> dict:
        return {
            "cn": self.cn,
            "objectClass": ["top", "group"],
            "sAMAccountName": self.account_name,
            "description": self.description or "No description.",  # LDAP doesn't allow empty strings, so we provide a default
            "groupType": int(GroupType.GLOBAL_SECURITY),
        }

    def create_in(self, destination: DestinationClient) -> None:
        destination.create_group(self)

    def add(self, member: DestinationModel, destination: DestinationClient) -> None:
        destination.add_to_group(member, self)

    @classmethod
    def from_raw_entry(cls, ou: str, entry: RawEntry) -> Group:
        return Group(entry.cn.value, ou, entry.sAMAccountName.value, entry.description.value)


@dataclass
class OrganizationalUnit(Entry):

    @property
    def dn(self) -> str:
        # NOTE: OUs use "OU=" instead of "CN=" in their DN
        return f"OU={self.cn},{self.ou}"

    @property
    def name(self) -> str:
        return self.cn

    def get_name(self) -> str:
        return self.name

    def serialize_for_creation(self) -> dict:
        return {
            "ou": self.cn,
            "objectClass": ["top", "organizationalUnit"],
        }

    @classmethod
    def from_raw_entry(cls, ou: str, entry: RawEntry) -> OrganizationalUnit:
        raise NotImplementedError  # TODO


@dataclass
class ADUser(Entry, DestinationUser):

    object_class: ClassVar[str] = "user"
    account_name: str
    first_name: str
    last_name: str
    password: Optional[str] = field(compare=False, default=None)

    @property
    def name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def get_name(self) -> str:
        return self.name

    @property
    def _encoded_password(self) -> bytes:
        if self.password is None:
            raise ValueError("Password must be set to encode.")

        return (f'"{self.password}"').encode("utf-16-le")

    def set_password(self, password: Optional[str], length: int = 12) -> None:
        self.password = password

    def set_random_password(self, length: int = 12) -> None:
        if length > 86:
            raise ValueError("Password length cannot exceed 86 characters.")

        self.set_password(secrets.token_urlsafe(64)[:length])

    def set_random_password_if_unset(self, length: int = 12) -> None:
        if not self.password:
            self.set_random_password(length)

    def serialize_for_creation(self) -> dict:
        return {
            "cn": self.cn,
            "sAMAccountName": self.account_name,
            "sn": self.last_name,
            "givenName": self.first_name,
            "displayName": f"{self.first_name} {self.last_name}",
            "objectClass": ["top", "person", "organizationalPerson", "user"],
            "unicodePwd": self._encoded_password,
            "userAccountControl": int(UserAccountControl.NORMAL_ACCOUNT),
        }

    @classmethod
    def from_raw_entry(cls, ou: str, entry: RawEntry) -> ADUser:
        return ADUser(entry.cn.value, ou, entry.sAMAccountName.value, entry.givenName.value, entry.sn.value, None)

    def create_in(self, destination: DestinationClient) -> None:
        destination.create_user(self)


