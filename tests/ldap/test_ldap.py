import os
from collections.abc import Generator

import pytest
from annotated_types import Ge
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
    ldap.create_ou(ou)
    yield ou
    ldap.delete_ou(ou)


@pytest.fixture
def member(ldap: Ldap, members_ou: OrganizationalUnit) -> Generator[User, None, None]:
    member = User(
        cn="s1234567",
        first_name="Nathan",
        last_name="Emanuel",
        password="P@ssword2026!",
        ou=os.environ["MEMBERS_OU"],
    )
    ldap.create_user(member)
    yield member
    ldap.delete_user(member)


@pytest.fixture
def committees_ou(ldap: Ldap) -> Generator[OrganizationalUnit, None, None]:
    ou = OrganizationalUnit(cn="Committees", ou=os.environ["BASE_OU"])
    ldap.create_ou(ou)
    yield ou
    ldap.delete_ou(ou)


@pytest.fixture
def committee(ldap: Ldap, committees_ou: OrganizationalUnit) -> Generator[Group, None, None]:
    committee = Group(
        cn="Test Committee",
        ou=os.environ["COMMITTEES_OU"],
        congressus_id=12345,
        description="This is a test committee.",
    )
    ldap.create_group(committee)
    yield committee
    ldap.delete_group(committee)


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
    ldap.create_ou(ou)
    ldap.delete_ou(ou)


@pytest.mark.integration
def test_create_committees_ou(ldap: Ldap) -> None:
    ou = OrganizationalUnit(cn="Committees", ou=os.environ["BASE_OU"])
    ldap.create_ou(ou)
    ldap.delete_ou(ou)


@pytest.mark.integration
def test_create_delete_user(ldap: Ldap, members_ou: OrganizationalUnit) -> None:
    member = User(
        cn="s1234567",
        first_name="Nathan",
        last_name="Emanuel",
        password="P@ssword2026!",
        ou=os.environ["MEMBERS_OU"],
    )
    ldap.create_user(member)
    ldap.delete_user(member)
    with pytest.raises(LdapConnectionError):
        ldap.delete_user(member)


@pytest.mark.integration
def test_disable_user(ldap: Ldap, member: User) -> None:
    ldap.disable_user(member.dn)


@pytest.mark.integration
def test_enable_user(ldap: Ldap, member: User) -> None:
    ldap.disable_user(member.dn)
    ldap.enable_user(member.dn)


@pytest.mark.integration
def test_create_delete_group(ldap: Ldap, committees_ou: OrganizationalUnit) -> None:
    committee = Group(
        cn="Test Committee",
        ou=os.environ["COMMITTEES_OU"],
        congressus_id=12345,
        description="This is a test committee.",
    )
    ldap.create_group(committee)
    ldap.delete_group(committee)
    with pytest.raises(LdapConnectionError):
        ldap.delete_group(committee)


@pytest.mark.integration
def test_add_to_remove_from_group(ldap: Ldap, member: User, committee: Group) -> None:
    ldap.add_to_group(member.dn, committee.dn)
    ldap.remove_from_group(member.dn, committee.dn)
