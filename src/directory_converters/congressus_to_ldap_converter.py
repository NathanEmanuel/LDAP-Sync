from directories.congressus import Group as CongressusGroup
from directories.congressus import Member as CongressusMember
from directories.ldap.models import Group as LdapGroup
from directories.ldap.models import User
from sync.types import DestinationGroup, DestinationUser, ModelConverter, SourceGroup, SourceUser


class CongressusToLdapConverter(ModelConverter):

    def __init__(self, base_ou: str, member_ou: str):
        self._base_ou = base_ou
        self._member_ou = member_ou

    def convert_group(self, group: SourceGroup) -> DestinationGroup:
        assert isinstance(group, CongressusGroup)  # not necessary, but helps with type checking and clarity
        return LdapGroup(
            cn=str(group.get_id()),
            ou=self._build_group_ou(group.model_dump()),
            name=group.name,
            description=group.description_short,
        )

    def _build_group_ou(self, data: dict) -> str:
        breadcrumbs = str(data["folder"]["breadcrumbs"])
        breadcrumbs = breadcrumbs.replace("Commitees", "Committees")
        ou_list = breadcrumbs.split(" / ")
        ou_list.reverse()
        ou_string = ",".join(f"OU={ou}" for ou in ou_list)
        return ou_string + f",{self._base_ou}"

    def convert_user(self, user: SourceUser) -> DestinationUser:
        assert isinstance(user, CongressusMember)  # not necessary, but helps with type checking and clarity
        ldap_user = User(
            cn=str(user.get_id()),
            ou=self._member_ou,
            account_name=user.username,
            first_name=user.first_name or user.nickname or "Unknown",
            last_name=user.last_name or "Unknown",
        )
        ldap_user.set_random_password_if_unset()
        return ldap_user
