from typing import Union, overload

from directories.active_directory.active_directory_client import ActiveDirectoryClient
from directories.active_directory.schemas import ADGroup, ADUser, Entry as ADEntry
from directories.congressus import GroupWithMemberships as CongressusGroup
from directories.congressus import Member as CongressusMember
from sync.types import DirectoryMapper, SourceGroup


class CongressusToActiveDirectoryMapper(
    DirectoryMapper[CongressusGroup, CongressusMember, ActiveDirectoryClient, ADGroup, ADUser]
):

    def __init__(self, base_ou: str, member_ou: str):
        self._base_ou = base_ou
        self._member_ou = member_ou

    @overload
    def convert(self, principal: SourceGroup[CongressusGroup, CongressusMember]) -> ADGroup: ...

    @overload
    def convert(self, principal: CongressusMember) -> ADUser: ...

    def convert(
        self, principal: Union[SourceGroup[CongressusGroup, CongressusMember], CongressusMember]
    ) -> Union[ADGroup, ADUser]:

        if isinstance(principal, CongressusGroup):
            return self._convert_group(principal)
        elif isinstance(principal, CongressusMember):
            return self._convert_user(principal)
        else:
            raise ValueError(f"Unsupported principal type: {type(principal)}")

    def _convert_group(self, group: CongressusGroup) -> ADGroup:

        member_dns = set()
        for m in group.get_members():
            member = self.convert(m)
            assert isinstance(member, ADEntry)
            member_dns.add(member.dn)

        return ADGroup(
            cn=str(group.get_id()),
            ou=self._build_group_ou(group.model_dump()),
            name=group.name,
            description=group.description_short,
            member_dns=member_dns,
        )

    def _build_group_ou(self, data: dict) -> str:
        breadcrumbs = str(data["folder"]["breadcrumbs"])
        breadcrumbs = breadcrumbs.replace("Commitees", "Committees")
        ou_list = breadcrumbs.split(" / ")
        ou_list.reverse()
        ou_string = ",".join(f"OU={ou}" for ou in ou_list)
        return ou_string + f",{self._base_ou}"

    def _convert_user(self, user: CongressusMember) -> ADUser:
        ad_user = ADUser(
            cn=str(user.get_id()),
            ou=self._member_ou,
            account_name=user.username,
            first_name=user.first_name or user.nickname or "Unknown",
            last_name=user.last_name or "Unknown",
        )
        ad_user.set_random_password_if_unset()
        return ad_user
