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

    @staticmethod
    def from_congressus_data(data: dict, base_ou: str):
        ou = Group.build_ou_from_congressus_data(data, base_ou)
        return Group(
            cn=data["name"],
            ou=ou,
            congressus_id=data["id"],
            description=data["description_short"],
        )

    @staticmethod
    def build_ou_from_congressus_data(data: dict, base_ou: str) -> str:
        breadcrumbs = str(data["folder"]["breadcrumbs"])
        breadcrumbs = breadcrumbs.replace("Commitees", "Committees")
        ou_list = breadcrumbs.split(" / ")
        ou_list.reverse()
        ou_string = ",".join(f"OU={ou}" for ou in ou_list)
        return ou_string + f",{base_ou}"
