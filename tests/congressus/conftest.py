import pytest

from congressus.models import Group, GroupMembership


@pytest.fixture
def sample_group_data() -> dict:
    return {
        "id": 90364,
        "name": "AXI 2024-2025",
        "folder_id": 2574,
        "folder": {
            "id": 2574,
            "name": "AXI",
            "parent_id": 1160,
            "breadcrumbs": "Commitees / AXI",
            "path": "commitees/axi",
            "published": True,
            "order_type": "lastname",
            "slug": "axi",
        },
        "address": {
            "country": {
                "id": 125,
                "calling_code": "31",
                "country_code": "NL",
                "name": "Netherlands",
                "name_local": "Nederland",
                "name_locale_en": "Netherlands",
                "name_locale_nl": "Nederland",
                "default_locale": {"id": 1, "code": "nl", "name": "Nederlands"},
            }
        },
        "memberships": [],
        "memo": "",
        "published": True,
        "slug": "axi-2024-2025",
        "path": "commitees/axi/axi-2024-2025",
        "start": "2025-01-24",
    }


@pytest.fixture
def sample_group(sample_group_data) -> Group:
    return Group.model_validate(sample_group_data)


@pytest.fixture
def sample_membership_data(sample_group_data: dict) -> dict:
    return {
        "id": 1,
        "member_id": 42,
        "start": "2025-01-24",
        "end": None,
        "function": "Chairman",
        "may_edit_profile": True,
        "may_manage_memberships": False,
        "may_manage_storage_objects": False,
        "is_self_enroll": False,
        "order_type": "lastname",
        "order": 1,
        "group_id": 90364,
        "group": sample_group_data,
    }


@pytest.fixture
def sample_group_membership(sample_membership_data) -> GroupMembership:
    return GroupMembership.model_validate(sample_membership_data)
