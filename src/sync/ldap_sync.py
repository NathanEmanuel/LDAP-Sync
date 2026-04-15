import logging

from congressus import CongressusClient
from congressus.models import Group as CongressusGroup
from congressus.models import GroupMembership as CongressusGroupMembership
from congressus.models import Member as CongressusMember
from ldap import LdapClient
from ldap.models import Group as LdapGroup
from ldap.models import User as LdapUser
from sync.factories import LdapModelFactory


class LdapSync:
    """
    Main class for syncing Congressus data to LDAP. This will be responsible for:
    - Fetching data from Congressus API
    - Transforming it into LDAP entries
    - Using LdapClient to create/update/delete entries in LDAP
    """

    def __init__(self, congressus_client: CongressusClient, ldap_client: LdapClient, ldap_model_factory: LdapModelFactory):
        self._congressus = congressus_client
        self._ldap = ldap_client
        self._ldap_model_factory = ldap_model_factory

    async def sync_all(self, dry_run: bool = False) -> None:
        active_committees = await self._congressus.list_active_committees()
        committee_ids = [int(committee.get_id()) for committee in active_committees]
        await self.sync_groups(committee_ids, dry_run=dry_run)

    async def sync_groups(self, group_ids: list[int], dry_run: bool = False) -> None:
        async for congressus_group in self._congressus.retrieve_groups(group_ids):

            if not dry_run:
                ldap_group = self.create_group(congressus_group, ignore_existing=True)
            else:
                ldap_group = self._ldap_model_factory.create_group_from_congressus_group(congressus_group)

            await self._sync_group_memberships(ldap_group, congressus_group.memberships, dry_run=dry_run)
            logging.info(f"Synced group: {congressus_group.name} (ID: {congressus_group.id})")

    async def _sync_group_memberships(
        self, ldap_group: LdapGroup, congressus_group_memberships: list[CongressusGroupMembership], dry_run: bool = False
    ) -> None:
        for membership in congressus_group_memberships:

            if not membership.is_active():
                continue

            member = await self._congressus.retrieve_member(membership.member_id)
            if not member.is_active():
                continue

            if not dry_run:
                ldap_user = self.create_account(member)
                self._ldap.add_to_group(ldap_user, ldap_group)
            else:
                logging.info(f"Would add member {member.first_name} {member.last_name} to group {ldap_group.get_name()}")

    def create_group(self, congressus_group: CongressusGroup, ignore_existing: bool = False) -> LdapGroup:
        ldap_group = self._ldap_model_factory.create_group_from_congressus_group(congressus_group)
        self._ldap.create(ldap_group, ignore_existing)
        return ldap_group

    def create_account(self, congressus_member: CongressusMember) -> LdapUser:
        user = self._ldap_model_factory.create_user_from_congressus_member(congressus_member)
        user.set_random_password_if_unset()
        self._ldap.create(user)
        return user

    # region Context Manager

    def __enter__(self):
        self._ldap.ldap_bind()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._ldap.ldap_unbind()

    # endregion
