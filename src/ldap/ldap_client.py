import logging
import ssl
from typing import Union

import ldap3.core.exceptions as ldap3_exceptions
from ldap3 import ALL, MODIFY_ADD, MODIFY_DELETE, MODIFY_REPLACE, Connection, Server
from ldap3.core.tls import Tls

from sync.types import DestinationClient, DestinationGroup, DestinationModel, DestinationUser

from .models import Entry, Group, User, UserAccountControl


class LdapClient(DestinationClient):

    _connection = None

    def __init__(self, admin_dn: str, admin_pw: str):
        self._admin_dn = admin_dn
        self._admin_pw = admin_pw

    # region Sync

    def create_group(self, group: DestinationGroup, ignore_existing: bool = False) -> bool:
        assert isinstance(group, Group)
        return self.create(group, ignore_existing, autocreate_ou=True)

    def create_user(self, user: DestinationUser, ignore_existing: bool = False) -> bool:
        assert isinstance(user, User)
        return self.create(user, ignore_existing, autocreate_ou=True)

    def add_to_group(self, member: DestinationModel, group: DestinationGroup) -> None:
        assert isinstance(member, (User, Group))
        assert isinstance(group, Group)
        member.create_in(self)
        self._add_to_group(member, group)

    # endregion

    def ldap_bind(self) -> None:
        tls = Tls(validate=ssl.CERT_NONE)  # ignore certificate validation
        server = Server("127.0.0.1", port=636, use_ssl=True, tls=tls, get_info=ALL)

        try:
            self._connection = Connection(
                server, user=self._admin_dn, password=self._admin_pw, auto_bind=True, raise_exceptions=True
            )
            logging.debug("Bound to Directory Server.")
        except ldap3_exceptions.LDAPBindError as e:
            logging.error(f"Failed to bind to Directory Server: {e}")

    def ldap_unbind(self) -> None:
        if self._connection:
            self._connection.unbind()
            self._connection = None
            logging.debug("Unbound from Directory Server.")

    def get_connection(self) -> Connection:
        if not self._connection:
            raise ldap3_exceptions.LDAPBindError(
                "Not connected to Directory Server. Use context manager or call ldap_bind() first."
            )

        return self._connection

    def create(self, entry: Entry, ignore_existing: bool = False, autocreate_ou: bool = False) -> bool:
        try:
            if autocreate_ou:
                self._create_ou(entry.ou, ignore_existing=True)

            self.get_connection().add(entry.dn, attributes=entry.serialize_for_creation())
            logging.info(f"Created {type(entry).__name__} {entry.get_name()}")
            return True
        except ldap3_exceptions.LDAPEntryAlreadyExistsResult:
            if ignore_existing:
                logging.debug(f"{type(entry).__name__} {entry.get_name()} already exists. Skipping creation.")
                return False
            raise

    def _create_ou(self, ou: str, ignore_existing: bool = False) -> bool:
        ou_components = ou.split(",")

        if not all(part.startswith("OU=") or part.startswith("DC=") for part in ou_components):
            raise ValueError(f"Invalid OU string: {ou}")

        try:
            self.get_connection().add(ou, attributes={"objectClass": ["top", "organizationalUnit"]})
            return True
        except ldap3_exceptions.LDAPEntryAlreadyExistsResult:
            if ignore_existing:
                logging.debug(f"OU {ou} already exists. Skipping creation.")
                return False
            raise
        except ldap3_exceptions.LDAPNoSuchObjectResult:
            self._create_ou(",".join(ou_components[1:]), ignore_existing)
            self.get_connection().add(ou, attributes={"objectClass": ["top", "organizationalUnit"]})
            return True

    def delete(self, entry: Entry) -> None:
        self.get_connection().delete(entry.dn)
        logging.info(f"Deleted {type(entry).__name__} {entry.get_name()}")

    def enable_user(self, user: User) -> None:
        self.modify_user_uac(user, UserAccountControl.NORMAL_ACCOUNT)

    def disable_user(self, user: User) -> None:
        self.modify_user_uac(user, (UserAccountControl.NORMAL_ACCOUNT | UserAccountControl.ACCOUNTDISABLE))

    def modify_user_uac(self, user: User, uac: UserAccountControl):
        self.get_connection().modify(user.dn, {"userAccountControl": [(MODIFY_REPLACE, [int(uac)])]})
        logging.info(f"Modified user {user.dn} with UAC {uac}")

    def _add_to_group(self, member: Union[User, Group], group: Group) -> None:
        self.get_connection().modify(group.dn, {"member": [(MODIFY_ADD, [member.dn])]})
        logging.info(f"Added {type(member).__name__} {member.get_name()} to {type(group).__name__} {group.get_name()}")

    def remove_from_group(self, member: Union[User, Group], group: Group) -> None:
        self.get_connection().modify(group.dn, {"member": [(MODIFY_DELETE, [member.dn])]})
        logging.info(f"Removed {type(member).__name__} {member.get_name()} from {type(group).__name__} {group.get_name()}")

    # region Context manager

    def __enter__(self):
        self.ldap_bind()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.ldap_unbind()

    # endregion
