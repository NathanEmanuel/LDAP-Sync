from congressus.models import Group as CongressusGroup
from congressus.models import Member as CongressusMember
from ldap.models import Group as LdapGroup
from ldap.models import User as LdapUser


class LdapModelFactory:

    def __init__(self, base_ou: str, member_ou: str):
        self._base_ou = base_ou
        self._member_ou = member_ou

    def create_user_from_congressus_member(self, member: CongressusMember) -> LdapUser:
        return LdapUser(
            cn=str(member.id),
            ou=self._member_ou,
            account_name=member.username,
            first_name=member.first_name or member.nickname or "Unknown",
            last_name=member.last_name or "Unknown",
        )

    def create_group_from_congressus_group(self, group: CongressusGroup) -> LdapGroup:
        ou = self._build_ou_from_congressus_data(group.model_dump())
        return LdapGroup(
            cn=str(group.id),
            ou=ou,
            name=group.name,
            description=group.description_short,
        )

    def _build_ou_from_congressus_data(self, data: dict) -> str:
        breadcrumbs = str(data["folder"]["breadcrumbs"])
        breadcrumbs = breadcrumbs.replace("Commitees", "Committees")
        ou_list = breadcrumbs.split(" / ")
        ou_list.reverse()
        ou_string = ",".join(f"OU={ou}" for ou in ou_list)
        return ou_string + f",{self._base_ou}"
