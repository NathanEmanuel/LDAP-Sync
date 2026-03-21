from dataclasses import dataclass

from models.group_type import GroupType
from models.ldap_entry import LdapEntry


@dataclass
class Group(LdapEntry):
    congressus_id: int
    description: str

    def serialize(self) -> dict:
        return {
            "cn": self.cn,
            "objectClass": ["top", "group"],
            "sAMAccountName": self.cn,
            "description": self.description,
            "groupType": int(GroupType.GLOBAL_SECURITY),
            "info": self.congressus_id,
        }
