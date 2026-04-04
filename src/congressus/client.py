from collections.abc import Awaitable, Callable
from datetime import date
from typing import TypeVar

import httpx

from congressus.models import *

T = TypeVar("T")
PAGE_REQUEST_LIMIT = 100


class Client:

    def __init__(self, base_url: str, api_key: str, committee_folder_id: int):
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
        )
        self._committee_folder_id = committee_folder_id

    async def _get(self, path: str, **params) -> dict:
        resp = await self._client.get(path, params=params)
        resp.raise_for_status()
        return resp.json()

    async def _depaginate(self, method: Callable[..., Awaitable[list[T]]], *args, **kwargs) -> list[T]:
        items: list[T] = list()

        for page in range(1, PAGE_REQUEST_LIMIT):
            new = await method(*args, page=page, **kwargs)
            if not new:
                break
            items.extend(new)
        else:
            raise RuntimeError("Too many pages requested. Stopping to avoid infinite loop.")

        return items

    # region Groups and Committees

    async def list_groups(self, folder_ids: list[int] = [], page: int = 1, page_size: int = 25) -> list[Group]:
        data = await self._get("/groups", folder_id=folder_ids, page=page, page_size=page_size)
        return [Group.model_validate(item) for item in data["data"]]

    async def list_standing_committees(self, page: int = 1, page_size: int = 25) -> list[Group]:
        return await self.list_groups(folder_ids=[self._committee_folder_id], page=page, page_size=page_size)

    async def list_annual_committees(self, page: int = 1, page_size: int = 25) -> list[Group]:
        response = await self._get("/group-folders/recursive")
        group_folders = [FolderWithChildren.model_validate(item) for item in response["data"]]
        committee_folder = next((folder for folder in group_folders if folder.id == self._committee_folder_id), None)
        if committee_folder is None:
            return []

        annual_committee_folders_ids = [folder.id for folder in committee_folder.children]
        return await self.list_groups(annual_committee_folders_ids, page=page, page_size=page_size)

    async def list_active_committees(self) -> list[Group]:
        committees = await self.list_active_standing_committees()
        committees.extend(await self.list_active_annual_committees())
        return committees

    async def list_active_standing_committees(self) -> list[Group]:
        committees = await self._depaginate(self.list_standing_committees)
        return [c for c in committees if c.end is None or c.end > date.today()]

    async def list_active_annual_committees(self) -> list[Group]:
        committees = await self._depaginate(self.list_annual_committees)
        return [c for c in committees if c.end is None or c.end > date.today()]

    async def retrieve_group(self, group_id: int) -> Group:
        data = await self._get(f"/groups/{group_id}")
        return Group.model_validate(data)
    
    # endregion
    
    # region Group Memberships

    async def list_group_memberships(self, group_ids: list[int] = [], member_ids: list[int] = [], page: int = 1, page_size: int = 25) -> list[GroupMembership]:
        data = await self._get("/groups/memberships", group_id=group_ids, member_id=member_ids, page=page, page_size=page_size)
        return [GroupMembership.model_validate(item) for item in data["data"]]

    async def list_active_committee_memberships(self) -> list[GroupMembership]:
        committees = await self.list_active_committees()
        committee_ids = [c.id for c in committees]
        memberships = await self._depaginate(self.list_group_memberships, group_ids=committee_ids)
        return [m for m in memberships if m.end is None or m.end > date.today()]
    
    async def list_active_member_ids(self) -> list[int]:
        memberships = await self.list_active_committee_memberships()
        member_ids = set(m.member_id for m in memberships)
        return list(member_ids)

    async def retrieve_group_membership(self, group_membership_id: int) -> GroupMembership:
        data = await self._get(f"/groups/memberships/{group_membership_id}")
        return GroupMembership.model_validate(data)

    # endregion

    # region Members

    async def retrieve_member(self, member_id: int) -> Member:
        data = await self._get(f"/members/{member_id}")
        return Member.model_validate(data)

    # endregion

    # region Context manager

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self._client.aclose()

    # endregion
