import logging
import ssl

import ldap3.core.exceptions as ldap3_exceptions
from ldap3 import ALL, MODIFY_ADD, MODIFY_DELETE, MODIFY_REPLACE, Connection, Server
from ldap3.core.tls import Tls

from .models import Entry, Group, User, UserAccountControl


class Ldap:

    _connection = None

    def __init__(self, admin_dn: str, admin_pw: str):
        self._admin_dn = admin_dn
        self._admin_pw = admin_pw

    def __enter__(self):
        self.ldap_bind()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.ldap_unbind()

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

    def createIfNotExists(self, entry: Entry, ignore_existing: bool = True) -> None:
        try:
            self.get_connection().add(entry.dn, attributes=entry.serialize())
        except ldap3_exceptions.LDAPEntryAlreadyExistsResult as e:
            if ignore_existing:
                logging.debug(f"{type(entry).__name__} {entry.getName()} already exists. Skipping creation.")
                return
            raise e

    def delete(self, entry: Entry) -> None:
        self.get_connection().delete(entry.dn)
        logging.debug(f"Deleted {type(entry).__name__} {entry.getName()}")

    def enable_user(self, user: User) -> None:
        self.modify_user_uac(user, UserAccountControl.NORMAL_ACCOUNT)

    def disable_user(self, user: User) -> None:
        self.modify_user_uac(user, (UserAccountControl.NORMAL_ACCOUNT | UserAccountControl.ACCOUNTDISABLE))

    def modify_user_uac(self, user: User, uac: UserAccountControl):
        self.get_connection().modify(user.dn, {"userAccountControl": [(MODIFY_REPLACE, [int(uac)])]})
        logging.debug(f"Modified user {user.dn} with UAC {uac}")

    def add_to_group(self, member: User | Group, group: Group) -> None:
        self.get_connection().modify(group.dn, {"member": [(MODIFY_ADD, [member.dn])]})
        logging.debug(f"Added {member.name} to {group.name}")

    def remove_from_group(self, member: User | Group, group: Group) -> None:
        self.get_connection().modify(group.dn, {"member": [(MODIFY_DELETE, [member.dn])]})
        logging.debug(f"Removed {member.name} from {group.name}")
