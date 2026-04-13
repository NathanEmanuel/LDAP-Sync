from dataclasses import dataclass

from ldap.models.entry import Entry


@dataclass
class OrganizationalUnit(Entry):

    @property
    def dn(self) -> str:
        # NOTE: OUs use "OU=" instead of "CN=" in their DN
        return f"OU={self.cn},{self.ou}"
    
    @property
    def name(self) -> str:
        return self.cn
    
    def getName(self) -> str:
        return self.name

    def serialize(self) -> dict:
        return {
            "ou": self.cn,
            "objectClass": ["top", "organizationalUnit"],
        }
