import os
from datetime import date

import httpx
from dotenv import load_dotenv

from congressus.models import FolderWithChildren, Group, GroupMembership, Member


class Client:
    def __init__(self, base_url: str, api_key: str):
        load_dotenv()
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
        )

    async def _get(self, path: str, **params) -> dict:
        resp = await self._client.get(path, params=params)
        resp.raise_for_status()
        return resp.json()

    async def list_groups(self, folder_ids: list[int] = [], page: int = 1) -> list[Group]:
        data = await self._get("/groups", folder_id=folder_ids, page=page)
        return [Group.model_validate(item) for item in data["data"]]

    async def list_standing_committees(self, page: int = 1) -> list[Group]:
        data = await self._get("/groups", folder_id=os.environ["CONGRESSUS_API_COMMITTEE_FOLDER_ID"], page=page)
        return [Group.model_validate(item) for item in data["data"]]

    async def list_active_standing_committees(self, page: int = 1) -> list[Group]:
        groups = await self.list_standing_committees(page=page)
        return [group for group in groups if group.end is None or group.end > date.today()]

    async def list_annual_committees(self, page: int = 1) -> list[Group]:
        response = await self._get("/group-folders/recursive")
        group_folders = [FolderWithChildren.model_validate(item) for item in response["data"]]
        committee_folder = next(
            (folder for folder in group_folders if folder.id == int(os.environ["CONGRESSUS_API_COMMITTEE_FOLDER_ID"])), None
        )
        if committee_folder is None:
            return []

        annual_committee_folders = [FolderWithChildren.model_validate(item) for item in committee_folder.children]
        annual_committee_folders_ids = [folder.id for folder in annual_committee_folders]
        return await self.list_groups(annual_committee_folders_ids, page=page)

    async def list_active_annual_committees(self, page: int = 1) -> list[Group]:
        annual_committees = await self.list_annual_committees(page=page)
        return [committee for committee in annual_committees if committee.end is None or committee.end > date.today()]

    async def retrieve_group(self, group_id: int) -> Group:
        data = await self._get(f"/groups/{group_id}")
        return Group.model_validate(data)

    async def list_group_memberships(self, group_id: list[int] = [], member_id: list[int] = []) -> list[GroupMembership]:
        data = await self._get("/groups/memberships", group_id=group_id, member_id=member_id)
        return [GroupMembership.model_validate(item) for item in data["data"]]

    async def retrieve_group_membership(self, group_membership_id: int) -> GroupMembership:
        data = await self._get(f"/groups/memberships/{group_membership_id}")
        return GroupMembership.model_validate(data)

    async def retrieve_member(self, member_id: int) -> Member:
        data = await self._get(f"/members/{member_id}")
        return Member.model_validate(data)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self._client.aclose()
