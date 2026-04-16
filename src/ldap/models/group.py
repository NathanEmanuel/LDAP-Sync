from dataclasses import dataclass
from enum import IntFlag
from typing import Optional

from ldap.models import Entry
from sync.types import DestinationClient, DestinationGroup, DestinationModel


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
class Group(Entry, DestinationGroup):

    name: str
    description: Optional[str]

    @property
    def account_name(self) -> str:
        return self.name.replace("/", "-")

    def get_name(self) -> str:
        return self.name

    def serialize_for_creation(self) -> dict:
        return {
            "cn": self.cn,
            "objectClass": ["top", "group"],
            "sAMAccountName": self.account_name,
            "description": self.description or "No description.",  # LDAP doesn't allow empty strings, so we provide a default
            "groupType": int(GroupType.GLOBAL_SECURITY),
        }

    def create_in(self, destination: DestinationClient) -> None:
        destination.create_group(self, ignore_existing=True)

    def add(self, member: DestinationModel, destination: DestinationClient) -> None:
        destination.add_to_group(member, self)
