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

from directories.active_directory import ActiveDirectoryClient
from directories.active_directory.schemas import Group, OrganizationalUnit, ADUser
from sync.exceptions import AlreadyExistsException, NoSuchGroupMemberException

load_dotenv()


@pytest.fixture
def ad() -> Generator[ActiveDirectoryClient, None, None]:
    with ActiveDirectoryClient(os.environ["ADMIN_DN"], os.environ["ADMIN_PW"]) as ad:
        yield ad


@pytest.fixture
def committees_ou(ad: ActiveDirectoryClient) -> Generator[OrganizationalUnit, None, None]:
    ou = OrganizationalUnit(cn="Committees", ou=os.environ["BASE_OU"])

    try:
        ad.create(ou, autocreate_ou=True)
    except LDAPEntryAlreadyExistsResult:
        pass

    yield ou

    ad.delete(ou)


@pytest.fixture
def members_ou(ad: ActiveDirectoryClient) -> Generator[OrganizationalUnit, None, None]:
    ou = OrganizationalUnit(cn="Members", ou=os.environ["BASE_OU"])

    try:
        ad.create(ou, autocreate_ou=True)
    except LDAPEntryAlreadyExistsResult:
        pass

    yield ou

    ad.delete(ou)


@pytest.fixture
def member(ad: ActiveDirectoryClient, members_ou: OrganizationalUnit) -> Generator[ADUser, None, None]:
    member = ADUser(
        cn="5678",
        account_name="s1234567",
        first_name="Nathan",
        last_name="Emanuel",
        password="P@ssword2026!",
        ou=members_ou.dn,
    )
    ad.create(member)
    yield member
    ad.delete(member)


@pytest.fixture
def committee(ad: ActiveDirectoryClient, committees_ou: OrganizationalUnit) -> Generator[Group, None, None]:
    committee = Group(
        cn="12345",
        ou=committees_ou.dn,
        name="Test Committee",
        description="This is a test committee.",
    )
    ad.create(committee)
    yield committee
    ad.delete(committee)


@pytest.mark.integration
def test_connection(ad: ActiveDirectoryClient) -> None:
    assert ad.get_connection().bound


@pytest.mark.integration
def test_invalid_credentials() -> None:
    with pytest.raises(LDAPInvalidCredentialsResult):
        with ActiveDirectoryClient("invalid_dn", "invalid_pw") as ad:
            pass


@pytest.mark.integration
def test_create_delete_user(ad: ActiveDirectoryClient, members_ou: OrganizationalUnit) -> None:
    member = ADUser(
        cn="5678",
        account_name="s1234567",
        first_name="Nathan",
        last_name="Emanuel",
        password="P@ssword2026!",
        ou=members_ou.dn,
    )

    try:
        ad.delete(member)
    except LDAPNoSuchObjectResult:
        pass

    with pytest.raises(LDAPNoSuchObjectResult):
        ad.delete(member)

    ad.create(member)
    with pytest.raises(LDAPEntryAlreadyExistsResult):
        ad.create(member)

    assert ad.is_synced(member)

    member.first_name = "First Name"
    member.last_name = "Last Name"
    assert not ad.is_synced(member)

    ad.delete(member)
    with pytest.raises(LDAPNoSuchObjectResult):
        ad.delete(member)


@pytest.mark.integration
def test_disable_user(ad: ActiveDirectoryClient, member: ADUser) -> None:
    ad.disable_user(member)
    ad.disable_user(member)


@pytest.mark.integration
def test_enable_user(ad: ActiveDirectoryClient, member: ADUser) -> None:
    ad.disable_user(member)
    ad.enable_user(member)
    ad.enable_user(member)
    ad.disable_user(member)
    ad.enable_user(member)


@pytest.mark.integration
def test_create_delete_group(ad: ActiveDirectoryClient, committees_ou: OrganizationalUnit) -> None:
    group = Group(
        cn="12345",
        ou=committees_ou.dn,
        name="Test Group",
        description="This is a test group.",
    )

    try:
        ad.delete(group)
    except LDAPNoSuchObjectResult:
        pass

    with pytest.raises(LDAPNoSuchObjectResult):
        ad.delete(group)

    ad.create(group)
    with pytest.raises(LDAPEntryAlreadyExistsResult):
        ad.create(group)

    assert ad.is_synced(group)

    group.name = "Updated Test Group"
    assert not ad.is_synced(group)

    ad.delete(group)
    with pytest.raises(LDAPNoSuchObjectResult):
        ad.delete(group)


@pytest.mark.integration
def test_add_to_remove_from_group(ad: ActiveDirectoryClient, member: ADUser, committee: Group) -> None:

    with pytest.raises(LDAPNoSuchAttributeResult):
        ad.remove_from_group(member, committee)

    ad.add_to_group(member, committee)
    with pytest.raises(AlreadyExistsException):
        ad.add_to_group(member, committee)

    ad.remove_from_group(member, committee)
    with pytest.raises(LDAPUnwillingToPerformResult):
        ad.remove_from_group(member, committee)

    fake_member = ADUser(
        cn="9999",
        account_name="s9999999",
        first_name="Fake",
        last_name="User",
        password="P@ssword2026!",
        ou=member.ou,
    )
    with pytest.raises(NoSuchGroupMemberException):
        ad.add_to_group(fake_member, committee)
