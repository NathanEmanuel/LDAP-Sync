import httpx

from congressus.models import Group, GroupMembership


class Client:
    def __init__(self, base_url: str, api_key: str):
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
        )

    async def _get(self, path: str, **params) -> dict:
        resp = await self._client.get(path, params=params)
        resp.raise_for_status()
        return resp.json()

    async def retrieve_group(self, group_id: int) -> Group:
        data = await self._get(f"/groups/{group_id}")
        return Group.model_validate(data)

    async def retrieve_group_membership(self, group_membership_id: int) -> GroupMembership:
        data = await self._get(f"/groups/memberships/{group_membership_id}")
        return GroupMembership.model_validate(data)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self._client.aclose()
