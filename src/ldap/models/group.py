from dataclasses import dataclass
from enum import IntFlag

from congressus.models import Group as CongressusGroup
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

    name: str
    description: str | None

    def get_name(self) -> str:
        return self.name

    def serialize_for_creation(self) -> dict:
        return {
            "cn": self.cn,
            "objectClass": ["top", "group"],
            "sAMAccountName": self.name,
            "description": self.description or "No description.",  # LDAP doesn't allow empty strings, so we provide a default
            "groupType": int(GroupType.GLOBAL_SECURITY),
        }

    @staticmethod
    def from_congressus_data(data: dict, base_ou: str):
        ou = Group.build_ou_from_congressus_data(data, base_ou)
        return Group(
            cn=data["id"],
            ou=ou,
            name=data["name"],
            description=data["description_short"],
        )
        
    @staticmethod
    def from_congressus_group(group: CongressusGroup, base_ou: str):
        ou = Group.build_ou_from_congressus_data(group.model_dump(), base_ou)
        return Group(
            cn=str(group.id),
            ou=ou,
            name=group.name,
            description=group.description_short or "No description.",
        )

    @staticmethod
    def build_ou_from_congressus_data(data: dict, base_ou: str) -> str:
        breadcrumbs = str(data["folder"]["breadcrumbs"])
        breadcrumbs = breadcrumbs.replace("Commitees", "Committees")
        ou_list = breadcrumbs.split(" / ")
        ou_list.reverse()
        ou_string = ",".join(f"OU={ou}" for ou in ou_list)
        return ou_string + f",{base_ou}"
