import os
from collections.abc import Generator

import pytest
from dotenv import load_dotenv
from ldap3.core.exceptions import (
    LDAPEntryAlreadyExistsResult,
    LDAPInvalidCredentialsResult,
    LDAPNoSuchAttributeResult,
    LDAPNoSuchObjectResult,
    LDAPUnwillingToPerformResult,
)

from directories.ldap import LdapClient
from directories.ldap.models import Group, OrganizationalUnit, User
from sync.exceptions import AlreadyExistsException, NoSuchGroupMemberException

load_dotenv()


@pytest.fixture
def ldap() -> Generator[LdapClient, None, None]:
    with LdapClient(os.environ["ADMIN_DN"], os.environ["ADMIN_PW"]) as ldap:
        yield ldap


@pytest.fixture
def committees_ou(ldap: LdapClient) -> Generator[OrganizationalUnit, None, None]:
    ou = OrganizationalUnit(cn="Committees", ou=os.environ["BASE_OU"])

    try:
        ldap.create(ou, autocreate_ou=True)
    except LDAPEntryAlreadyExistsResult:
        pass

    yield ou

    ldap.delete(ou)


@pytest.fixture
def members_ou(ldap: LdapClient) -> Generator[OrganizationalUnit, None, None]:
    ou = OrganizationalUnit(cn="Members", ou=os.environ["BASE_OU"])

    try:
        ldap.create(ou, autocreate_ou=True)
    except LDAPEntryAlreadyExistsResult:
        pass

    yield ou

    ldap.delete(ou)


@pytest.fixture
def member(ldap: LdapClient, members_ou: OrganizationalUnit) -> Generator[User, None, None]:
    member = User(
        cn="5678",
        account_name="s1234567",
        first_name="Nathan",
        last_name="Emanuel",
        password="P@ssword2026!",
        ou=members_ou.dn,
    )
    ldap.create(member)
    yield member
    ldap.delete(member)


@pytest.fixture
def committee(ldap: LdapClient, committees_ou: OrganizationalUnit) -> Generator[Group, None, None]:
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
def test_ldap_connection(ldap: LdapClient) -> None:
    assert ldap.get_connection().bound


@pytest.mark.integration
def test_ldap_invalid_credentials() -> None:
    with pytest.raises(LDAPInvalidCredentialsResult):
        with LdapClient("invalid_dn", "invalid_pw") as ldap:
            pass


@pytest.mark.integration
def test_create_delete_user(ldap: LdapClient, members_ou: OrganizationalUnit) -> None:
    member = User(
        cn="5678",
        account_name="s1234567",
        first_name="Nathan",
        last_name="Emanuel",
        password="P@ssword2026!",
        ou=members_ou.dn,
    )
    
    with pytest.raises(LDAPNoSuchObjectResult):
        ldap.delete(member)

    ldap.create(member)
    with pytest.raises(LDAPEntryAlreadyExistsResult):
        ldap.create(member)

    ldap.delete(member)
    with pytest.raises(LDAPNoSuchObjectResult):
        ldap.delete(member)


@pytest.mark.integration
def test_disable_user(ldap: LdapClient, member: User) -> None:
    ldap.disable_user(member)
    ldap.disable_user(member)


@pytest.mark.integration
def test_enable_user(ldap: LdapClient, member: User) -> None:
    ldap.disable_user(member)
    ldap.enable_user(member)
    ldap.enable_user(member)
    ldap.disable_user(member)
    ldap.enable_user(member)


@pytest.mark.integration
def test_create_delete_group(ldap: LdapClient, committees_ou: OrganizationalUnit) -> None:
    committee = Group(
        cn="12345",
        ou=committees_ou.dn,
        name="Test Committee",
        description="This is a test committee.",
    )

    with pytest.raises(LDAPNoSuchObjectResult):
        ldap.delete(committee)

    ldap.create(committee)
    with pytest.raises(LDAPEntryAlreadyExistsResult):
        ldap.create(committee)

    ldap.delete(committee)
    with pytest.raises(LDAPNoSuchObjectResult):
        ldap.delete(committee)


@pytest.mark.integration
def test_add_to_remove_from_group(ldap: LdapClient, member: User, committee: Group) -> None:

    with pytest.raises(LDAPNoSuchAttributeResult):
        ldap.remove_from_group(member, committee)

    ldap.add_to_group(member, committee)
    with pytest.raises(AlreadyExistsException):
        ldap.add_to_group(member, committee)

    ldap.remove_from_group(member, committee)
    with pytest.raises(LDAPUnwillingToPerformResult):
        ldap.remove_from_group(member, committee)
        
    fake_member = User(
        cn="9999",
        account_name="s9999999",
        first_name="Fake",
        last_name="User",
        password="P@ssword2026!",
        ou=member.ou,
    )
    with pytest.raises(NoSuchGroupMemberException):
        ldap.add_to_group(fake_member, committee)
