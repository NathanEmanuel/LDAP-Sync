from __future__ import annotations

import logging
import ssl
from abc import ABC, abstractmethod
from typing import ClassVar, Type, TypeVar

from ldap3 import ALL, LEVEL, Connection
from ldap3 import Entry as RawEntry
from ldap3 import ObjectDef, Reader, Server, Tls
from ldap3.core.exceptions import (
    LDAPBindError,
    LDAPEntryAlreadyExistsResult,
    LDAPNoSuchObjectResult,
    LDAPNotAllowedOnNotLeafResult,
)

from sync.exceptions import AlreadyExistsException
from sync.types import DestinationDirectory

ENTRY_TYPE = TypeVar("ENTRY_TYPE", bound="ADEntry")


class ADEntry(ABC):

    object_class: ClassVar[str]
    ou: str

    def get_object_class(self) -> str:
        return self.object_class

    def get_ou(self) -> str:
        return self.ou

    @abstractmethod
    def get_dn(self) -> str: ...

    @abstractmethod
    def fetch_children(self, directory: ActiveDirectoryClient) -> list[ADEntry]: ...

    @abstractmethod
    def serialize_for_creation(self) -> dict: ...

    @classmethod
    @abstractmethod
    def from_raw_entry(cls: Type[ENTRY_TYPE], entry: RawEntry) -> ENTRY_TYPE: ...


class ActiveDirectoryClient(DestinationDirectory):

    _connection = None

    def __init__(self, admin_dn: str, admin_pw: str):
        self._admin_dn = admin_dn
        self._admin_pw = admin_pw

    def __enter__(self):
        self.bind()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.unbind()

    # region Connection

    def bind(self) -> None:
        tls = Tls(validate=ssl.CERT_NONE)  # ignore certificate validation
        server = Server("127.0.0.1", port=636, use_ssl=True, tls=tls, get_info=ALL)

        try:
            self._connection = Connection(
                server, user=self._admin_dn, password=self._admin_pw, auto_bind=True, raise_exceptions=True
            )
            logging.debug("Bound to Directory Server.")
        except LDAPBindError as e:
            logging.error(f"Failed to bind to Directory Server: {e}")
            raise

    def unbind(self) -> None:
        if self._connection:
            self._connection.unbind()
            self._connection = None
            logging.debug("Unbound from Directory Server.")

    def get_connection(self) -> Connection:
        if not self._connection:
            raise LDAPBindError("Not connected to Directory Server. Use context manager or call bind() first.")

        return self._connection

    # endregion

    # region CRUD

    def fetch(self, entry: ENTRY_TYPE) -> ENTRY_TYPE:
        obj = ObjectDef(entry.object_class, self.get_connection())
        obj += "sAMAccountName"
        obj += "member"  # for groups, will be ignored for users
        reader = Reader(self.get_connection(), obj, entry.get_dn())
        reader.search()
        return entry.from_raw_entry(reader[0])

    def fetch_children(self, entry: ADEntry) -> list[RawEntry]:
        conn = self.get_connection()
        conn.search(
            search_base=entry.get_dn(),
            search_filter="(objectClass=*)",
            search_scope=LEVEL,
            attributes=["objectClass", "cn", "givenName", "sn", "sAMAccountName", "member"],
        )
        return conn.entries

    def create(self, entry: ADEntry, autocreate_ou: bool = False, ignore_existing: bool = False) -> None:
        if autocreate_ou:
            self._create_ou(entry.get_ou(), ignore_existing=True)

        try:
            self.get_connection().add(entry.get_dn(), entry.get_object_class(), attributes=entry.serialize_for_creation())
        except LDAPEntryAlreadyExistsResult as e:
            if ignore_existing:
                logging.debug(f"Entry {entry.get_dn()} already exists. Skipping creation.")
                return
            raise AlreadyExistsException from e

    def _create_ou(self, ou: str, ignore_existing: bool = False) -> bool:
        ou_components = ou.split(",")

        if not all(part.startswith("OU=") or part.startswith("DC=") for part in ou_components):
            raise ValueError(f"Invalid OU string: {ou}")

        try:
            self.get_connection().add(ou, "organizationalUnit", attributes={"objectClass": ["top", "organizationalUnit"]})
            return True
        except LDAPEntryAlreadyExistsResult:
            if ignore_existing:
                logging.debug(f"OU {ou} already exists. Skipping creation.")
                return False
            raise
        except LDAPNoSuchObjectResult:
            self._create_ou(",".join(ou_components[1:]), ignore_existing)
            self.get_connection().add(ou, "organizationalUnit", attributes={"objectClass": ["top", "organizationalUnit"]})
            return True

    def modify(self, entry: ADEntry, changes: dict) -> None:
        try:
            self.get_connection().modify(entry.get_dn(), changes)
        except LDAPEntryAlreadyExistsResult as e:
            raise AlreadyExistsException from e

    def delete(self, entry: ADEntry, ignore_nonexistent: bool = False, recursive: bool = False) -> None:
        try:
            self.get_connection().delete(entry.get_dn())
        except LDAPNoSuchObjectResult:
            if ignore_nonexistent:
                logging.debug(f"Entry {entry.get_dn()} does not exist. Skipping deletion.")
                return
            raise
        except LDAPNotAllowedOnNotLeafResult:
            if not recursive:
                raise

            children = entry.fetch_children(self)
            for child in children:
                self.delete(child, recursive=True)

            self.delete(entry)

    # endregion
