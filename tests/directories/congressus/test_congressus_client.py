from collections.abc import AsyncGenerator
from datetime import date

import httpx
import pytest
import respx

from directories.congressus import CongressusClient
from directories.congressus.models import Group, GroupMembership

BASE_URL = "https://api.congressus.nl/v30"
FOLDER_ID = 123


@pytest.fixture
async def client() -> AsyncGenerator[CongressusClient, None]:
    async with CongressusClient(BASE_URL, api_key="test-key", committee_folder_id=FOLDER_ID) as c:
        yield c


@respx.mock
async def test_retrieve_group(client: CongressusClient, sample_group_data: dict) -> None:
    respx.get(f"{BASE_URL}/groups/90364").mock(return_value=httpx.Response(200, json=sample_group_data))

    result = await client.retrieve_group(90364)

    assert isinstance(result, Group)
    assert result.id == 90364
    assert result.name == "AXI 2024-2025"
    assert result.folder.name == "AXI"  # type: ignore
    assert result.address.country.country_code == "NL"  # type: ignore


@respx.mock
async def test_retrieve_group_not_found(client: CongressusClient) -> None:
    respx.get(f"{BASE_URL}/groups/0").mock(return_value=httpx.Response(404))
    with pytest.raises(httpx.HTTPStatusError):
        await client.retrieve_group(0)


@respx.mock
async def test_list_standing_committees(client: CongressusClient, sample_active_standing_committee_data: dict) -> None:

    respx.get(f"{BASE_URL}/groups").mock(return_value=httpx.Response(200, json=sample_active_standing_committee_data))

    result = await client.list_standing_committees()

    assert isinstance(result, list)
    assert all(isinstance(g, Group) for g in result)
    assert len(result) == 2
    assert result[0].name == "AcquisiCie"
    assert result[1].name == "AlmanaCie"
    assert result[0].id == 66187
    assert result[1].id == 43387


@respx.mock
async def test_list_active_standing_committees(client: CongressusClient, sample_active_standing_committee_data: dict) -> None:

    respx.get(f"{BASE_URL}/groups", params={"folder_id": FOLDER_ID, "page": 1}).mock(
        return_value=httpx.Response(200, json=sample_active_standing_committee_data)
    )
    respx.get(f"{BASE_URL}/groups", params={"folder_id": FOLDER_ID, "page": 2}).mock(
        return_value=httpx.Response(200, json={"data": [], "total": 0})
    )

    result = await client.list_active_standing_committees()

    assert isinstance(result, list)
    assert all(isinstance(g, Group) for g in result)
    assert len(result) == 1
    assert result[0].name == "AcquisiCie"
    assert result[0].id == 66187


@respx.mock
async def test_retrieve_group_membership(client: CongressusClient, sample_membership_data: dict) -> None:
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
async def test_retrieve_group_membership_not_found(client: CongressusClient) -> None:
    respx.get(f"{BASE_URL}/groups/memberships/0").mock(return_value=httpx.Response(404))
    with pytest.raises(httpx.HTTPStatusError):
        await client.retrieve_group_membership(0)


@respx.mock
async def test_retrieve_member(client: CongressusClient, sample_member_data: dict) -> None:
    respx.get(f"{BASE_URL}/members/1965").mock(return_value=httpx.Response(200, json=sample_member_data))

    result = await client.retrieve_member(1965)

    assert result.id == 1965
    assert result.first_name == "John"
    assert result.last_name == "Doe"
    assert result.date_of_birth == date(1970, 1, 1)
    assert result.email == "john.doe@example.com"
