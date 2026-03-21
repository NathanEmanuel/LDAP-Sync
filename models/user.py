from dataclasses import dataclass

from models.user_account_control import UserAccountControl


@dataclass
class User:
    username: str
    first_name: str
    last_name: str
    password: str
    organizational_unit: str

    @property
    def dn(self) -> str:
        return f'CN={self.first_name} {self.last_name},{self.organizational_unit}'

    @property
    def encoded_password(self) -> bytes:
        return (f'"{self.password}"').encode('utf-16-le')

    def to_ldap(self) -> dict:
        return {
            'cn':                 f'{self.first_name} {self.last_name}',
            'sn':                 self.last_name,
            'givenName':          self.first_name,
            'sAMAccountName':     self.username,
            'objectClass':        ['top', 'person', 'organizationalPerson', 'user'],
            'unicodePwd':         self.encoded_password,
            'userAccountControl': int(UserAccountControl.NORMAL_ACCOUNT),
        }
