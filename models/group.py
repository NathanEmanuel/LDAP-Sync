from dataclasses import dataclass

from models.group_type import GroupType


@dataclass
class Group:
    name: str
    ou: str
    congressus_id: int
    description: str

    @property
    def dn(self) -> str:
        return f'CN={self.name},{self.ou}'

    def to_ldap(self) -> dict:
        return {
            'cn':               self.name,
            'objectClass':      ['top', 'group'],
            'sAMAccountName':   self.name,
            'description':      self.description,
            'groupType':        int(GroupType.GLOBAL_SECURITY),
            'info':             self.congressus_id,
        }
