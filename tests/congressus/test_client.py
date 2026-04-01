from collections.abc import AsyncGenerator
from datetime import date

import httpx
import pytest
import respx

from congressus.client import Client
from congressus.models import Group, GroupMembership

BASE_URL = "https://api.congressus.nl/v30"


@pytest.fixture
async def client() -> AsyncGenerator[Client, None]:
    async with Client(BASE_URL, api_key="test-key") as c:
        yield c


@respx.mock
async def test_retrieve_group(client: Client, sample_group_data: dict) -> None:
    respx.get(f"{BASE_URL}/groups/90364").mock(return_value=httpx.Response(200, json=sample_group_data))

    result = await client.retrieve_group(90364)

    assert isinstance(result, Group)
    assert result.id == 90364
    assert result.name == "AXI 2024-2025"
    assert result.folder.name == "AXI"
    assert result.address.country.country_code == "NL"
    

@respx.mock
async def test_retrieve_group_not_found(client: Client) -> None:
    respx.get(f"{BASE_URL}/groups/0").mock(return_value=httpx.Response(404))
    with pytest.raises(httpx.HTTPStatusError):
        await client.retrieve_group(0)


@respx.mock
async def test_retrieve_group_membership(client: Client, sample_membership_data: dict) -> None:
    respx.get(f"{BASE_URL}/groups/memberships/1").mock(return_value=httpx.Response(200, json=sample_membership_data))

    result = await client.retrieve_group_membership(1)

    assert isinstance(result, GroupMembership)
    assert result.id == 1
    assert result.member_id == 42
    assert result.function == "Chairman"
    assert result.group.name == "AXI 2024-2025"
    assert result.start == date(2025, 1, 24)
    assert result.end is None
    assert result.may_manage_memberships is False


@respx.mock
async def test_retrieve_group_membership_not_found(client: Client) -> None:
    respx.get(f"{BASE_URL}/groups/memberships/0").mock(return_value=httpx.Response(404))
    with pytest.raises(httpx.HTTPStatusError):
        await client.retrieve_group_membership(0)
