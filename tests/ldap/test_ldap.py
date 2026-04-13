import os
from collections.abc import Generator

import pytest
from dotenv import load_dotenv

from ldap.ldap import Ldap, LdapConnectionError
from ldap.models.group import Group
from ldap.models.organizational_unit import OrganizationalUnit
from ldap.models.user import User

load_dotenv()


@pytest.fixture
def ldap() -> Generator[Ldap, None, None]:
    with Ldap(os.environ["ADMIN_DN"], os.environ["ADMIN_PW"]) as ldap:
        yield ldap


@pytest.fixture
def members_ou(ldap: Ldap) -> Generator[OrganizationalUnit, None, None]:
    ou = OrganizationalUnit(cn="Members", ou=os.environ["BASE_OU"])
    ldap.create(ou)
    yield ou
    ldap.delete(ou)


@pytest.fixture
def member(ldap: Ldap, members_ou: OrganizationalUnit) -> Generator[User, None, None]:
    member = User(
        cn="5678",
        student_number="s1234567",
        first_name="Nathan",
        last_name="Emanuel",
        password="P@ssword2026!",
        ou=members_ou.dn,
    )
    ldap.create(member)
    yield member
    ldap.delete(member)


@pytest.fixture
def committees_ou(ldap: Ldap) -> Generator[OrganizationalUnit, None, None]:
    ou = OrganizationalUnit(cn="Committees", ou=os.environ["BASE_OU"])
    ldap.create(ou)
    yield ou
    ldap.delete(ou)


@pytest.fixture
def committee(ldap: Ldap, committees_ou: OrganizationalUnit) -> Generator[Group, None, None]:
    committee = Group(
        cn="12345",
        ou=committees_ou.dn,
        name="Test Committee",
        description="This is a test committee.",
    )
    ldap.create(committee)
    yield committee
    ldap.delete(committee)


@pytest.mark.integration
def test_ldap_connection(ldap: Ldap) -> None:
    assert ldap.get_ldap_connection().bound


@pytest.mark.integration
def test_ldap_invalid_credentials() -> None:
    with pytest.raises(LdapConnectionError):
        with Ldap("invalid_dn", "invalid_pw") as ldap:
            pass


@pytest.mark.integration
def test_create_members_ou(ldap: Ldap) -> None:
    ou = OrganizationalUnit(cn="Members", ou=os.environ["BASE_OU"])
    ldap.create(ou)
    ldap.delete(ou)


@pytest.mark.integration
def test_create_committees_ou(ldap: Ldap) -> None:
    ou = OrganizationalUnit(cn="Committees", ou=os.environ["BASE_OU"])
    ldap.create(ou)
    ldap.delete(ou)


@pytest.mark.integration
def test_create_delete_user(ldap: Ldap, members_ou: OrganizationalUnit) -> None:
    member = User(
        cn="5678",
        student_number="s1234567",
        first_name="Nathan",
        last_name="Emanuel",
        password="P@ssword2026!",
        ou=members_ou.dn,
    )
    ldap.create(member)
    ldap.delete(member)
    with pytest.raises(LdapConnectionError):
        ldap.delete(member)


@pytest.mark.integration
def test_disable_user(ldap: Ldap, member: User) -> None:
    ldap.disable_user(member)


@pytest.mark.integration
def test_enable_user(ldap: Ldap, member: User) -> None:
    ldap.disable_user(member)
    ldap.enable_user(member)


@pytest.mark.integration
def test_create_delete_group(ldap: Ldap, committees_ou: OrganizationalUnit) -> None:
    committee = Group(
        cn="12345",
        ou=committees_ou.dn,
        name="Test Committee",
        description="This is a test committee.",
    )
    ldap.create(committee)
    ldap.delete(committee)
    with pytest.raises(LdapConnectionError):
        ldap.delete(committee)


@pytest.mark.integration
def test_add_to_remove_from_group(ldap: Ldap, member: User, committee: Group) -> None:
    ldap.add_to_group(member, committee)
    ldap.remove_from_group(member, committee)
