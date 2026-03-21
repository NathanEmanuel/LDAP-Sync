from dataclasses import dataclass

from models.ldap_entry import LdapEntry
from models.user_account_control import UserAccountControl


@dataclass
class User(LdapEntry):
    first_name: str
    last_name: str
    password: str

    @property
    def dn(self) -> str:
        return f"CN={self.cn},{self.ou}"

    @property
    def encoded_password(self) -> bytes:
        return (f'"{self.password}"').encode("utf-16-le")

    def serialize(self) -> dict:
        return {
            "cn": self.cn,
            "sn": self.last_name,
            "givenName": self.first_name,
            "sAMAccountName": self.cn,
            "objectClass": ["top", "person", "organizationalPerson", "user"],
            "unicodePwd": self.encoded_password,
            "userAccountControl": int(UserAccountControl.NORMAL_ACCOUNT),
        }
