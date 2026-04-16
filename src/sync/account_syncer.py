import asyncio
import logging

from sync.types import DestinationClient, DestinationGroup, DestinationModel, ModelConverter, SourceClient, SourceGroup


class AccountSyncer:

    def __init__(self, source_client: SourceClient, destination_client: DestinationClient, model_converter: ModelConverter):
        self._source = source_client
        self._destination = destination_client
        self._model_converter = model_converter
        self._user_locks: dict[int, asyncio.Lock] = {}

    async def sync_all(self, dry_run: bool = False) -> None:
        groups = await self._source.get_groups()
        await self._sync_groups(list(groups), dry_run=dry_run)

    async def _sync_groups(self, groups: list[SourceGroup], dry_run: bool = False) -> None:
        tasks = [self._sync_group(group, dry_run) for group in groups]
        if tasks:
            await asyncio.gather(*tasks)

    async def _sync_group(self, source_group: SourceGroup, dry_run: bool = False) -> None:
        destination_group = self._model_converter.convert_group(source_group)

        if not dry_run:
            self._destination.create_group(destination_group, ignore_existing=True)

        await self._sync_group_memberships(source_group, dry_run=dry_run)

        logging.info(f"Synced group: {destination_group.get_name()} (ID: {destination_group.get_id()})")

    async def _sync_group_memberships(self, source_group: SourceGroup, dry_run: bool = False) -> None:
        destination_group = self._model_converter.convert_group(source_group)
        tasks = []
        async for source_member in await self._source.get_group_members(source_group):

            if dry_run:
                logging.info(f"Would sync {source_member.get_name()} to {source_group.get_name()}")
                continue

            destination_member = source_member.convert_with(self._model_converter)
            tasks.append(asyncio.create_task(self._sync_member_to_group(destination_member, destination_group)))

        if tasks:
            await asyncio.gather(*tasks)

    async def _sync_member_to_group(self, member: DestinationModel, group: DestinationGroup) -> None:
        async with self._get_destination_lock(int(member.get_id())):
            group.add(member, self._destination)

    def _get_destination_lock(self, id: int) -> asyncio.Lock:
        if id not in self._user_locks:
            self._user_locks[id] = asyncio.Lock()
        return self._user_locks[id]

    # region Context Manager

    async def __aenter__(self) -> "AccountSyncer":
        self._destination.__enter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        self._destination.__exit__(exc_type, exc_val, exc_tb)

    # endregion
