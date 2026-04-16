import asyncio
import logging

import ldap3.core.exceptions

from congressus import CongressusClient
from congressus.models import Group as CongressusGroup
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
        self._user_locks: dict[int, asyncio.Lock] = {}

    async def sync_all(self, dry_run: bool = False) -> None:
        active_committees = await self._congressus.list_active_committees()
        await self._sync_groups(active_committees, dry_run=dry_run)

    async def _sync_groups(self, groups: list[CongressusGroup], dry_run: bool = False) -> None:
        tasks = [self._sync_group(group, dry_run) for group in groups]
        if tasks:
            await asyncio.gather(*tasks)

    async def _sync_group(self, congressus_group: CongressusGroup, dry_run: bool = False) -> None:
        if not dry_run:
            ldap_group = self.create_group(congressus_group, ignore_existing=True)
        else:
            ldap_group = self._ldap_model_factory.create_group_from_congressus_group(congressus_group)

        await self._sync_group_memberships(ldap_group, dry_run=dry_run)

        logging.info(f"Synced group: {congressus_group.name} (ID: {congressus_group.id})")

    async def _sync_group_memberships(self, ldap_group: LdapGroup, dry_run: bool = False) -> None:
        tasks = []
        async for member in self._congressus.list_groups_active_members(int(ldap_group.get_id())):

            if dry_run:
                logging.info(f"Would sync {member.first_name} {member.last_name} to {ldap_group.get_name()}")
                continue

            tasks.append(asyncio.create_task(self._sync_member_to_group(member, ldap_group)))

        if tasks:
            await asyncio.gather(*tasks)

    async def _sync_member_to_group(self, member: CongressusMember, ldap_group: LdapGroup) -> None:
        async with self._get_user_lock(member.id):
            try:
                ldap_user = self.create_account(member)
            except ldap3.core.exceptions.LDAPEntryAlreadyExistsResult:
                ldap_user = self._ldap_model_factory.create_user_from_congressus_member(member)

            self._ldap.add_to_group(ldap_user, ldap_group)

    def _get_user_lock(self, member_id: int) -> asyncio.Lock:
        if member_id not in self._user_locks:
            self._user_locks[member_id] = asyncio.Lock()
        return self._user_locks[member_id]

    def create_group(self, congressus_group: CongressusGroup, ignore_existing: bool = False) -> LdapGroup:
        ldap_group = self._ldap_model_factory.create_group_from_congressus_group(congressus_group)
        self._ldap.create(ldap_group, ignore_existing, autocreate_ou=True)
        return ldap_group

    def create_account(self, congressus_member: CongressusMember) -> LdapUser:
        user = self._ldap_model_factory.create_user_from_congressus_member(congressus_member)
        user.set_random_password_if_unset()
        self._ldap.create(user, autocreate_ou=True)
        return user

    # region Context Manager

    def __enter__(self):
        self._ldap.ldap_bind()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._ldap.ldap_unbind()

    # endregion
