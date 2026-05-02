from __future__ import annotations

import logging
import secrets
from dataclasses import dataclass, field
from typing import ClassVar, Optional, Union

from ldap3 import MODIFY_ADD, MODIFY_DELETE, MODIFY_REPLACE
from ldap3 import Entry as RawEntry
from ldap3.core.exceptions import LDAPNoSuchObjectResult

from directories.active_directory.active_directory_client import ActiveDirectoryClient, Entry
from directories.active_directory.enums import GroupType, UserAccountControl
from sync.exceptions import NoSuchGroupMemberException
from sync.types import DestinationGroup, DestinationUser


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
class ADGroup(Entry, DestinationGroup):

    object_class: ClassVar[str] = "group"
    name: str
    description: Optional[str]
    member_dns: set[str]

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

    @classmethod
    def from_raw_entry(cls, ou: str, entry: RawEntry) -> ADGroup:
        return ADGroup(
            entry.cn.value,
            ou,
            entry.sAMAccountName.value,
            entry.description.value,
            set(entry.member.values),
        )

    def is_synced_in(self, destination: ActiveDirectoryClient) -> bool:
        remote_self = self.fetch_in(destination)
        return remote_self == self

    def fetch_in(self, destination: ActiveDirectoryClient) -> ADGroup:
        return destination.fetch(self)

    def create_in(self, destination: ActiveDirectoryClient) -> None:
        destination.create(self, autocreate_ou=True)
        logging.info(f"Created group {self.get_name()}")

    def add_member_in(self, directory: ActiveDirectoryClient, member: Union[ADGroup, ADUser]) -> None:
        try:
            directory.modify(self, {"member": [(MODIFY_ADD, [member.dn])]})
            self.member_dns.add(member.dn)
            logging.info(f"Added {member.get_name()} to group {self.get_name()}")
        except LDAPNoSuchObjectResult as e:
            raise NoSuchGroupMemberException from e

    def remove_member_in(self, directory: ActiveDirectoryClient, member: Union[ADGroup, ADUser]) -> None:
        try:
            directory.modify(self, {"member": [(MODIFY_DELETE, [member.dn])]})
            self.member_dns.remove(member.dn)
            logging.info(f"Removed {member.get_name()} from group {self.get_name()}")
        except LDAPNoSuchObjectResult as e:
            raise NoSuchGroupMemberException from e


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

    def is_synced_in(self, destination: ActiveDirectoryClient) -> bool:
        remote_self = self.fetch_in(destination)
        return remote_self == self

    def fetch_in(self, destination: ActiveDirectoryClient) -> ADUser:
        return destination.fetch(self)

    def create_in(self, destination: ActiveDirectoryClient) -> None:
        destination.create(self, autocreate_ou=True)
        logging.info(f"Created user {self.get_name()}")

    def modify_uac_in(self, directory: ActiveDirectoryClient, uac: UserAccountControl) -> None:
        directory.modify(self, {"userAccountControl": [(MODIFY_REPLACE, [int(uac)])]})

    def enable_in(self, directory: ActiveDirectoryClient) -> None:
        self.modify_uac_in(directory, UserAccountControl.NORMAL_ACCOUNT)
        logging.info(f"Enabled user {self.get_name()}")

    def disable_in(self, directory: ActiveDirectoryClient) -> None:
        self.modify_uac_in(directory, UserAccountControl.NORMAL_ACCOUNT | UserAccountControl.ACCOUNTDISABLE)
        logging.info(f"Disabled user {self.get_name()}")
