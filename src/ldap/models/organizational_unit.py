from dataclasses import dataclass

from ldap.models.entry import Entry


@dataclass
class OrganizationalUnit(Entry):
    @property
    def dn(self) -> str:
        return f"OU={self.cn},{self.ou}"

    def serialize(self) -> dict:
        return {
            "ou": self.cn,
            "objectClass": ["top", "organizationalUnit"],
        }
