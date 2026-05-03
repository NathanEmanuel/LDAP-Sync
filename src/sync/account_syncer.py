from __future__ import annotations

import asyncio
import logging
from types import TracebackType
from typing import Generic, Union, cast

from sync.exceptions import AlreadyExistsException, NoSuchGroupMemberException
from sync.types import (
    DESTINATION_DIR_TYPE,
    DESTINATION_GROUP_TYPE,
    DESTINATION_USER_TYPE,
    SOURCE_GROUP_TYPE,
    SOURCE_USER_TYPE,
    DestinationGroup,
    DestinationPrincipal,
    DestinationUser,
    DirectoryMapper,
    SourceDirectory,
    SourceGroup,
)


class PrincipalSyncer(
    Generic[SOURCE_GROUP_TYPE, SOURCE_USER_TYPE, DESTINATION_DIR_TYPE, DESTINATION_GROUP_TYPE, DESTINATION_USER_TYPE]
):

    def __init__(
        self,
        source_directory: SourceDirectory[SOURCE_GROUP_TYPE, SOURCE_USER_TYPE],
        destination_directory: DESTINATION_DIR_TYPE,
        directory_mapper: DirectoryMapper[
            SOURCE_GROUP_TYPE, SOURCE_USER_TYPE, DESTINATION_DIR_TYPE, DESTINATION_GROUP_TYPE, DESTINATION_USER_TYPE
        ],
    ):
        self._source_directory = source_directory
        self._destination_directory = destination_directory
        self._directory_mapper = directory_mapper
        self._user_locks: dict[int, asyncio.Lock] = {}

    async def sync_all(self, dry_run: bool = False) -> None:
        logging.info("Starting a full sync...")
        source_groups = await self._source_directory.get_groups()
        await self._sync_groups(list(source_groups), dry_run=dry_run)
        logging.info("Full sync completed.")

    async def _sync_groups(self, source_groups: list[SOURCE_GROUP_TYPE], dry_run: bool = False) -> None:
        tasks = [self._sync_group(g, dry_run) for g in source_groups]
        if tasks:
            await asyncio.gather(*tasks)

    async def _sync_group(self, source_group: SourceGroup[SOURCE_GROUP_TYPE, SOURCE_USER_TYPE], dry_run: bool = False) -> None:
        destination_group = self._directory_mapper.convert(source_group)

        if not dry_run:
            try:
                destination_group.create_in(self._destination_directory)
            except AlreadyExistsException:
                logging.debug(f"Group {destination_group.get_name()} already exists. Skipping creation.")

        await self._sync_group_memberships(source_group, dry_run)

        logging.debug(f"Synced group: {destination_group.get_name()} (ID: {destination_group.get_id()})")

    async def _sync_group_memberships(
        self, source_group: SourceGroup[SOURCE_GROUP_TYPE, SOURCE_USER_TYPE], dry_run: bool = False
    ) -> None:

        destination_group = self._directory_mapper.convert(source_group)
        tasks = []
        for source_member in source_group.get_members():

            if dry_run:
                logging.info(f"Would sync {source_member.get_name()} to {source_group.get_name()}")
                continue

            destination_member = self._directory_mapper.convert(source_member)
            tasks.append(asyncio.create_task(self._sync_member_to_group(destination_member, destination_group)))

        await asyncio.gather(*tasks)

    async def _sync_member_to_group(
        self,
        member: Union[
            DestinationGroup[DESTINATION_DIR_TYPE, DESTINATION_GROUP_TYPE, DESTINATION_USER_TYPE],
            DestinationUser[DESTINATION_DIR_TYPE],
        ],
        group: DestinationGroup[DESTINATION_DIR_TYPE, DESTINATION_GROUP_TYPE, DESTINATION_USER_TYPE],
    ) -> None:

        async with self._get_destination_lock(int(member.get_id())):

            # TODO remove this when migrating to Python 3.12+
            member = cast(Union[DESTINATION_GROUP_TYPE, DESTINATION_USER_TYPE], member)

            try:
                group.add_member_in(self._destination_directory, member)
            except NoSuchGroupMemberException:
                logging.debug(f"{member.get_name()} does not exist. Creating account and adding to {group.get_name()}...")
                await self._create_group_member(member)
                group.add_member_in(self._destination_directory, member)
            except AlreadyExistsException:
                logging.debug(f"{member.get_name()} is already a member of {group.get_name()}. Skipping.")

    async def _create_group_member(self, member: DestinationPrincipal[DESTINATION_DIR_TYPE]) -> None:
        member.create_in(self._destination_directory)

    def _get_destination_lock(self, id: int) -> asyncio.Lock:
        if id not in self._user_locks:
            self._user_locks[id] = asyncio.Lock()
        return self._user_locks[id]

    # region Context Manager

    async def __aenter__(
        self,
    ) -> PrincipalSyncer[
        SOURCE_GROUP_TYPE, SOURCE_USER_TYPE, DESTINATION_DIR_TYPE, DESTINATION_GROUP_TYPE, DESTINATION_USER_TYPE
    ]:
        self._destination_directory.__enter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self._destination_directory.__exit__(exc_type, exc_val, exc_tb)

    # endregion
