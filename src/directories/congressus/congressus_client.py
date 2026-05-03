import asyncio
import math
from collections.abc import AsyncIterator, Awaitable
from datetime import date
from typing import Generic, Protocol, TypeVar

import httpx

from directories.congressus.models import *
from sync.types import SourceDirectory

T = TypeVar("T")
PAGE_SIZE = 100
PAGE_REQUEST_LIMIT = 10


class Page(BaseModel, Generic[T]):
    data: list[T]
    total: int


class PaginatedCallable(Protocol[T]):
    def __call__(self, *args, page: int = 1, **kwargs) -> Awaitable[Page[T]]: ...


class CongressusClient(SourceDirectory[GroupWithMemberships, Member]):

    def __init__(
        self,
        base_url: str,
        api_key: str,
        committee_folder_id: int,
        http_timeout_configuration: Optional[httpx.Timeout] = None,
        http_limit_configuration: Optional[httpx.Limits] = None,
    ):
        self._committee_folder_id = committee_folder_id
        http_timeout_configuration = http_timeout_configuration or httpx.Timeout(10.0)
        http_limit_configuration = http_limit_configuration or httpx.Limits(max_connections=50)

        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=http_timeout_configuration,
            limits=http_limit_configuration,
        )

    # region Sync

    async def get_groups(self):
        groups = await self.list_active_committees()
        tasks = [self._get_group_with_members(g) for g in groups]
        return await asyncio.gather(*tasks)

    async def _get_group_with_members(self, group: Group) -> GroupWithMemberships:
        group = await self.retrieve_group(int(group.get_id()))
        members = {m async for m in self.list_groups_active_members(int(group.get_id()))}
        group.set_members(members)
        return group

    # endregion

    # region Private

    async def _get(self, path: str, **params) -> dict:
        resp = await self._client.get(path, params=params)
        resp.raise_for_status()
        return resp.json()

    async def _depaginate(self, method: PaginatedCallable[T], *args, **kwargs) -> list[T]:
        first = await method(*args, page=1, **kwargs)

        if not first.data:
            return []

        total_pages = min(math.ceil(first.total / PAGE_SIZE), PAGE_REQUEST_LIMIT)

        if total_pages == 1:
            return first.data

        rest = await asyncio.gather(*[method(*args, page=p, **kwargs) for p in range(2, total_pages + 1)])

        return first.data + [item for page in rest for item in page.data]

    # endregion

    # region Groups and Members

    async def list_groups(self, *, folder_ids: list[int] = [], page: int = 1) -> Page[Group]:
        data = await self._get("/groups", folder_id=folder_ids, page=page, page_size=PAGE_SIZE)
        return Page[Group].model_validate(data)

    async def list_standing_committees(self) -> list[Group]:
        return await self._depaginate(self.list_groups, folder_ids=[self._committee_folder_id])

    async def list_annual_committees(self) -> list[Group]:
        response = await self._get("/group-folders/recursive")
        group_folders = [FolderWithChildren.model_validate(item) for item in response["data"]]
        committee_folder = next((folder for folder in group_folders if folder.id == self._committee_folder_id), None)
        if committee_folder is None:
            return []

        annual_committee_folders_ids = [folder.id for folder in committee_folder.children]
        return await self._depaginate(self.list_groups, folder_ids=annual_committee_folders_ids)

    async def list_active_committees(self) -> list[Group]:
        standing, annual = await asyncio.gather(self.list_active_standing_committees(), self.list_active_annual_committees())
        return standing + annual

    async def _filter_active(self, group: list[Group]) -> list[Group]:
        return [g for g in group if g.end is None or g.end > date.today()]

    async def list_active_standing_committees(self) -> list[Group]:
        return await self._filter_active(await self.list_standing_committees())

    async def list_active_annual_committees(self) -> list[Group]:
        return await self._filter_active(await self.list_annual_committees())

    async def retrieve_group(self, group_id: int) -> GroupWithMemberships:
        data = await self._get(f"/groups/{group_id}")
        return GroupWithMemberships.model_validate(data)

    async def retrieve_member(self, member_id: int) -> Member:
        data = await self._get(f"/members/{member_id}")
        return Member.model_validate(data)

    async def retrieve_groups(self, group_ids: list[int]) -> AsyncIterator[GroupWithMemberships]:
        for group in asyncio.as_completed([self.retrieve_group(id) for id in group_ids]):
            yield await group

    async def retrieve_members(self, member_ids: list[int]) -> AsyncIterator[Member]:
        for member in asyncio.as_completed([self.retrieve_member(id) for id in member_ids]):
            yield await member

    # endregion

    # region Group Memberships

    async def list_group_memberships(
        self, *, group_ids: list[int] = [], member_ids: list[int] = [], page: int = 1
    ) -> Page[GroupMembership]:
        data = await self._get("/groups/memberships", group_id=group_ids, member_id=member_ids, page=page, page_size=PAGE_SIZE)
        return Page[GroupMembership].model_validate(data)

    async def list_groups_active_memberships(self, group_id: int) -> list[GroupMembership]:
        memberships = await self._depaginate(self.list_group_memberships, group_ids=[group_id])
        return [m for m in memberships if m.end is None or m.end > date.today()]

    async def list_groups_active_members(self, group_id: int) -> AsyncIterator[Member]:
        memberships = await self.list_groups_active_memberships(group_id)
        async for member in self.retrieve_members([ms.member_id for ms in memberships]):
            if member.is_current():
                yield member

    async def list_active_committee_memberships(self) -> list[GroupMembership]:
        committees = await self.list_active_committees()
        committee_ids = [c.id for c in committees]
        memberships = await self._depaginate(self.list_group_memberships, group_ids=committee_ids)
        return [m for m in memberships if m.end is None or m.end > date.today()]

    async def list_active_members(self) -> AsyncIterator[Member]:
        memberships = await self.list_active_committee_memberships()
        unique_member_ids = list({m.member_id for m in memberships})
        async for member in self.retrieve_members(unique_member_ids):
            if member.is_current():
                yield member

    async def retrieve_group_membership(self, group_membership_id: int) -> GroupMembershipWithGroup:
        data = await self._get(f"/groups/memberships/{group_membership_id}")
        return GroupMembershipWithGroup.model_validate(data)

    # endregion

    # region Context manager

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self._client.aclose()

    # endregion
