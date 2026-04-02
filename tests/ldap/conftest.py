import os

import pytest
from dotenv import load_dotenv

from ldap.models.group import Group
from ldap.models.user import User

load_dotenv()

@pytest.fixture
def member() -> User:
    return User(
        cn="s1234567",
        first_name="Nathan",
        last_name="Emanuel",
        password="P@ssword2026!",
        ou=os.environ["MEMBERS_OU"],
    )

@pytest.fixture
def committee() -> Group:
    return Group(
        cn="Test Committee",
        ou=os.environ["COMMITTEES_OU"],
        congressus_id=12345,
        description="This is a test committee.",
    )