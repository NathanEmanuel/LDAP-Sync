import secrets
from dataclasses import dataclass
from enum import IntFlag
from typing import Optional

from directories.ldap.models import Entry
from sync.types import DestinationClient, DestinationUser


class UserAccountControl(IntFlag):
    SCRIPT = 0x0001
    ACCOUNTDISABLE = 0x0002
    HOMEDIR_REQUIRED = 0x0008
    LOCKOUT = 0x0010
    PASSWD_NOTREQD = 0x0020
    PASSWD_CANT_CHANGE = 0x0040
    ENCRYPTED_TEXT_PWD_ALLOWED = 0x0080
    TEMP_DUPLICATE_ACCOUNT = 0x0100
    NORMAL_ACCOUNT = 0x0200
    INTERDOMAIN_TRUST_ACCOUNT = 0x0800
    WORKSTATION_TRUST_ACCOUNT = 0x1000
    SERVER_TRUST_ACCOUNT = 0x2000
    DONT_EXPIRE_PASSWORD = 0x10000
    MNS_LOGON_ACCOUNT = 0x20000
    SMARTCARD_REQUIRED = 0x40000
    TRUSTED_FOR_DELEGATION = 0x80000
    NOT_DELEGATED = 0x100000
    USE_DES_KEY_ONLY = 0x200000
    DONT_REQ_PREAUTH = 0x400000
    PASSWORD_EXPIRED = 0x800000
    TRUSTED_TO_AUTH_FOR_DELEGATION = 0x1000000
    PARTIAL_SECRETS_ACCOUNT = 0x4000000


@dataclass
class User(Entry, DestinationUser):
    account_name: str
    first_name: str
    last_name: str
    password: Optional[str] = None

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

    def create_in(self, destination: DestinationClient, ignore_existing: bool = False) -> None:
        destination.create_user(self, ignore_existing)
