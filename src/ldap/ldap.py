import ssl

import ldap3.core.exceptions
from ldap3 import ALL, MODIFY_ADD, MODIFY_DELETE, MODIFY_REPLACE
from ldap3 import Connection as LdapConnection
from ldap3 import Server
from ldap3.core.tls import Tls

from ldap.models.entry import Entry
from ldap.models.group import Group
from ldap.models.user import User, UserAccountControl


class Ldap:

    _ldap_connection = None

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
            self._ldap_connection = LdapConnection(server, user=self._admin_dn, password=self._admin_pw, auto_bind=True)
            print("Bound to Directory Server.")
        except ldap3.core.exceptions.LDAPBindError as e:
            raise LdapConnectionError("Failed to bind to Directory Server.")

    def ldap_unbind(self) -> None:
        if self._ldap_connection:
            self._ldap_connection.unbind()
            self._ldap_connection = None
            print("Unbound from Directory Server.")

    def get_ldap_connection(self) -> LdapConnection:
        if not self._ldap_connection:
            raise LdapConnectionError("Not connected to Directory Server. Call ldap_bind() first.")

        return self._ldap_connection

    def create(self, entry: Entry) -> None:
        self.get_ldap_connection().add(entry.dn, attributes=entry.serialize())
        self._assert_ldap_successful()
        print(f"Created {type(entry).__name__} {entry.getName()}")

    def delete(self, entry: Entry) -> None:
        self.get_ldap_connection().delete(entry.dn)
        self._assert_ldap_successful()
        print(f"Deleted {type(entry).__name__} {entry.getName()}")

    def enable_user(self, user: User) -> None:
        self.modify_user_uac(user, UserAccountControl.NORMAL_ACCOUNT)

    def disable_user(self, user: User) -> None:
        self.modify_user_uac(user, (UserAccountControl.NORMAL_ACCOUNT | UserAccountControl.ACCOUNTDISABLE))

    def modify_user_uac(self, user: User, uac: UserAccountControl):
        self.get_ldap_connection().modify(user.dn, {"userAccountControl": [(MODIFY_REPLACE, [int(uac)])]})
        self._assert_ldap_successful()
        print(f"Modified user {user.dn} with UAC {uac}")

    def add_to_group(self, member: User | Group, group: Group) -> None:
        self.get_ldap_connection().modify(group.dn, {"member": [(MODIFY_ADD, [member.dn])]})
        self._assert_ldap_successful()
        print(f"Added {member.name} to {group.name}")

    def remove_from_group(self, member: User | Group, group: Group) -> None:
        self.get_ldap_connection().modify(group.dn, {"member": [(MODIFY_DELETE, [member.dn])]})
        self._assert_ldap_successful()
        print(f"Removed {member.name} from {group.name}")

    def get_ldap_result_description(self) -> str:
        return self.get_ldap_connection().result["description"]

    def _is_ldap_successful(self) -> bool:
        return self.get_ldap_connection().result["result"] == 0

    def _assert_ldap_successful(self) -> None:
        if not self._is_ldap_successful():
            raise LdapConnectionError(f"LDAP operation failed: {self.get_ldap_result_description()}")


class LdapConnectionError(Exception):
    pass
