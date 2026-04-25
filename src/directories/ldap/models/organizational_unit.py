from __future__ import annotations

from dataclasses import dataclass

from ldap3 import Entry as RawEntry

from directories.ldap.models import Entry


@dataclass
class OrganizationalUnit(Entry):

    @property
    def dn(self) -> str:
        # NOTE: OUs use "OU=" instead of "CN=" in their DN
        return f"OU={self.cn},{self.ou}"

    @property
    def name(self) -> str:
        return self.cn

    def get_name(self) -> str:
        return self.name

    def serialize_for_creation(self) -> dict:
        return {
            "ou": self.cn,
            "objectClass": ["top", "organizationalUnit"],
        }

    @classmethod
    def from_raw_entry(cls, ou: str, entry: RawEntry) -> OrganizationalUnit:
        raise NotImplementedError  # TODO
