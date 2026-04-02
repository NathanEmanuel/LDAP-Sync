from dataclasses import dataclass
from enum import IntFlag

from ldap.models.entry import Entry


class GroupType(IntFlag):
    GLOBAL = 0x00000002
    DOMAIN_LOCAL = 0x00000004
    UNIVERSAL = 0x00000008
    SECURITY = 0x80000000

    # Common combinations
    GLOBAL_SECURITY = GLOBAL | SECURITY
    DOMAIN_LOCAL_SECURITY = DOMAIN_LOCAL | SECURITY
    UNIVERSAL_SECURITY = UNIVERSAL | SECURITY
    GLOBAL_DISTRIBUTION = GLOBAL
    DOMAIN_LOCAL_DISTRIBUTION = DOMAIN_LOCAL
    UNIVERSAL_DISTRIBUTION = UNIVERSAL


@dataclass
class Group(Entry):
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
