import os

from dotenv import load_dotenv
import ldap3.core.exceptions
from ldap3 import Server, ALL, MODIFY_ADD, MODIFY_REPLACE
from ldap3 import Connection as LdapConnection
from ldap3.core.tls import Tls
import ssl

from models.group import Group
from models.user import User
from models.user_account_control import UserAccountControl


class Sync:

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

    def create_user(self, user: User) -> None:
        if self.get_ldap_connection().add(user.dn, attributes=user.to_ldap()):
            print(f"Created user {user.dn}")
        else:
            raise LdapConnectionError(f"Error creating user {user.dn}: {self.get_ldap_connection().result}")

    def enable_user(self, dn: str) -> None:
        self.modify_user_uac(dn, UserAccountControl.NORMAL_ACCOUNT)

    def disable_user(self, dn: str) -> None:
        self.modify_user_uac(dn, (UserAccountControl.NORMAL_ACCOUNT | UserAccountControl.ACCOUNTDISABLE))

    def modify_user_uac(self, dn: str, uac: UserAccountControl):
        self.get_ldap_connection().modify(dn, {"userAccountControl": [(MODIFY_REPLACE, [int(uac)])]})

        if self.get_ldap_connection().result["result"] == 0:
            print(f"Modified user {dn} with UAC {uac}")
        else:
            raise LdapConnectionError(f"Error modifying user {dn}: {self.get_ldap_connection().result}")
        
    def create_group(self, group: Group) -> None:
        if self.get_ldap_connection().add(group.dn, attributes=group.to_ldap()):
            print(f"Created group {group.dn}")
        else:
            raise LdapConnectionError(f"Error creating group {group.dn}: {self.get_ldap_connection().result}")
        
    def add_to_group(self, group_member_dn: str, group_dn: str) -> None:
        self.get_ldap_connection().modify(group_dn, {"member": [(MODIFY_ADD, [group_member_dn])]})

        if self.get_ldap_connection().result["result"] == 0:
            print(f"Added {group_member_dn} to group {group_dn}")
        else:
            raise LdapConnectionError(f"Error adding {group_member_dn} to group {group_dn}: {self.get_ldap_connection().result}")

    def remove_from_group(self, group_member_dn: str, group_dn: str) -> None:
        self.get_ldap_connection().modify(group_dn, {"member": [(MODIFY_REPLACE, [group_member_dn])]})

        if self.get_ldap_connection().result["result"] == 0:
            print(f"Removed {group_member_dn} from group {group_dn}")
        else:
            raise LdapConnectionError(f"Error removing {group_member_dn} from group {group_dn}: {self.get_ldap_connection().result}")

class LdapConnectionError(Exception):
    pass


def main():
    load_dotenv()

    member = User(
        username="TestUser",
        first_name="Test",
        last_name="User",
        password="P@ssword2026!",
        organizational_unit=os.environ['MEMBERS_OU'],
    )

    try:
        with Sync(os.environ['ADMIN_DN'], os.environ['ADMIN_PW']) as sync:
            # sync.create_user(member)
            # sync.disable_user(member.dn)
            sync.enable_user(member.dn)
    except LdapConnectionError as e:
        print(e)


if __name__ == "__main__":
    main()
