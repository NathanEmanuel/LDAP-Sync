from __future__ import annotations

from abc import ABC, abstractmethod
import logging
import secrets
from dataclasses import dataclass, field
from typing import ClassVar, Optional, Union

from ldap3 import MODIFY_ADD, MODIFY_DELETE, MODIFY_REPLACE
from ldap3 import Entry as RawEntry
from ldap3.core.exceptions import LDAPNoSuchObjectResult

from directories.active_directory.active_directory_client import ActiveDirectoryClient, ADEntry
from directories.active_directory.enums import GroupType, UserAccountControl
from sync.exceptions import NoSuchGroupMemberException
from sync.types import DestinationGroup, DestinationUser


class EntryParser:

    @staticmethod
    def from_raw_entry(entry: RawEntry) -> ADEntry:
        object_classes = entry.objectClass
        if "organizationalUnit" in object_classes:
            return OrganizationalUnit.from_raw_entry(entry)
        elif "group" in object_classes:
            return ADGroup.from_raw_entry(entry)
        elif "user" in object_classes:
            return ADUser.from_raw_entry(entry)
        else:
            raise ValueError(f"Unknown object class: {object_classes}")


@dataclass
class OrganizationalUnit(ADEntry):

    object_class: ClassVar[str] = "organizationalUnit"

    def __init__(self, dn: str):
        self.ou = dn

    def get_dn(self) -> str:
        return self.ou

    def fetch_children(self, directory: ActiveDirectoryClient) -> list[ADEntry]:
        children = directory.fetch_children(self)
        return [EntryParser.from_raw_entry(child) for child in children]

    def serialize_for_creation(self) -> dict:
        return {
            "objectClass": ["top", "organizationalUnit"],
        }

    @classmethod
    def from_raw_entry(cls, entry: RawEntry) -> OrganizationalUnit:
        return OrganizationalUnit(entry.entry_dn)


class ADPrincipal(ADEntry, ABC):

    object_class: ClassVar[str] = "top"
    cn: str

    def get_cn(self) -> str:
        return self.cn

    @abstractmethod
    def get_account_name(self) -> str: ...

    def fetch_children(self, directory: ActiveDirectoryClient) -> list[ADEntry]:
        raise NotImplementedError("Active Directory principals do not have children.")

    @staticmethod
    def _parse_dn(dn: str) -> tuple[str, str]:
        parts = dn.split(",")
        cn = parts[0].removeprefix("CN=").removeprefix("cn=")
        ou = ",".join(parts[1:])
        return cn, ou


@dataclass
class ADGroup(ADPrincipal, DestinationGroup):

    object_class: ClassVar[str] = "group"
    name: str
    description: Optional[str]
    member_dns: set[str]

    def __init__(self, dn: str, name: str, description: Optional[str], member_dns: set[str]):
        self.cn, self.ou = self._parse_dn(dn)
        self.name = name
        self.description = description
        self.member_dns = member_dns

    # ADPrincipal methods

    @classmethod
    def from_raw_entry(cls, entry: RawEntry) -> ADGroup:
        return ADGroup(
            dn=entry.entry_dn,
            name=entry.sAMAccountName.value,
            description=entry.description.value,
            member_dns=set(entry.member.values),
        )

    def get_dn(self) -> str:
        return f"CN={self.cn},{self.ou}"

    def get_account_name(self) -> str:
        return self.name.replace("/", "-")

    def serialize_for_creation(self) -> dict:
        return {
            "cn": self.get_cn(),
            "objectClass": ["top", "group"],
            "sAMAccountName": self.get_account_name(),
            "description": self.description or "No description.",  # LDAP doesn't allow empty strings, so we provide a default
            "groupType": int(GroupType.GLOBAL_SECURITY),
        }

    # DestinationGroup interface methods

    def get_id(self) -> str:
        return self.get_cn()

    def get_name(self) -> str:
        return self.get_account_name()

    def is_synced_in(self, directory: ActiveDirectoryClient) -> bool:
        remote_self = self.fetch_in(directory)
        return remote_self == self

    def fetch_in(self, directory: ActiveDirectoryClient) -> ADGroup:
        return directory.fetch(self)

    def create_in(self, directory: ActiveDirectoryClient) -> None:
        directory.create(self, autocreate_ou=True)
        logging.info(f"Created group {self.get_name()}")

    def add_member_in(self, directory: ActiveDirectoryClient, member: Union[ADGroup, ADUser]) -> None:
        try:
            directory.modify(self, {"member": [(MODIFY_ADD, [member.get_dn()])]})
            self.member_dns.add(member.get_dn())
            logging.info(f"Added {member.get_name()} to group {self.get_name()}")
        except LDAPNoSuchObjectResult as e:
            raise NoSuchGroupMemberException from e

    def remove_member_in(self, directory: ActiveDirectoryClient, member: Union[ADGroup, ADUser]) -> None:
        try:
            directory.modify(self, {"member": [(MODIFY_DELETE, [member.get_dn()])]})
            self.member_dns.remove(member.get_dn())
            logging.info(f"Removed {member.get_name()} from group {self.get_name()}")
        except LDAPNoSuchObjectResult as e:
            raise NoSuchGroupMemberException from e


@dataclass
class ADUser(ADPrincipal, DestinationUser):

    object_class: ClassVar[str] = "user"
    account_name: str
    first_name: str
    last_name: str
    password: Optional[str] = field(compare=False, default=None)

    def __init__(self, dn: str, account_name: str, first_name: str, last_name: str, password: Optional[str] = None):
        self.cn, self.ou = self._parse_dn(dn)
        self.account_name = account_name
        self.first_name = first_name
        self.last_name = last_name
        self.password = password

    # ADPrincipal methods

    @classmethod
    def from_raw_entry(cls, entry: RawEntry) -> ADUser:
        return ADUser(
            dn=entry.entry_dn,
            account_name=entry.sAMAccountName.value,
            first_name=entry.givenName.value,
            last_name=entry.sn.value,
            password=None,
        )

    def get_dn(self) -> str:
        return f"CN={self.cn},{self.ou}"

    def get_account_name(self) -> str:
        return self.account_name

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

    # DestinationUser interface methods

    def get_id(self) -> str:
        return self.get_cn()

    def get_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def is_synced_in(self, directory: ActiveDirectoryClient) -> bool:
        remote_self = self.fetch_in(directory)
        return remote_self == self

    def fetch_in(self, directory: ActiveDirectoryClient) -> ADUser:
        return directory.fetch(self)

    def create_in(self, directory: ActiveDirectoryClient) -> None:
        directory.create(self, autocreate_ou=True)
        logging.info(f"Created user {self.get_name()}")

    # Specific methods

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

    def modify_uac_in(self, directory: ActiveDirectoryClient, uac: UserAccountControl) -> None:
        directory.modify(self, {"userAccountControl": [(MODIFY_REPLACE, [int(uac)])]})

    def enable_in(self, directory: ActiveDirectoryClient) -> None:
        self.modify_uac_in(directory, UserAccountControl.NORMAL_ACCOUNT)
        logging.info(f"Enabled user {self.get_name()}")

    def disable_in(self, directory: ActiveDirectoryClient) -> None:
        self.modify_uac_in(directory, UserAccountControl.NORMAL_ACCOUNT | UserAccountControl.ACCOUNTDISABLE)
        logging.info(f"Disabled user {self.get_name()}")
