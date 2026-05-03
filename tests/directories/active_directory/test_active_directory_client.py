import os
from collections.abc import Generator

import pytest
from dotenv import load_dotenv
from ldap3.core.exceptions import (
    LDAPInvalidCredentialsResult,
    LDAPNoSuchAttributeResult,
    LDAPNoSuchObjectResult,
    LDAPUnwillingToPerformResult,
)

from directories.active_directory import ActiveDirectoryClient
from directories.active_directory.schemas import ADGroup, OrganizationalUnit, ADUser
from sync.exceptions import AlreadyExistsException, NoSuchGroupMemberException

load_dotenv()


@pytest.fixture
def directory() -> Generator[ActiveDirectoryClient, None, None]:
    with ActiveDirectoryClient(os.environ["ADMIN_DN"], os.environ["ADMIN_PW"]) as ad:
        yield ad


@pytest.fixture
def committees_ou(directory: ActiveDirectoryClient) -> Generator[OrganizationalUnit, None, None]:
    ou = OrganizationalUnit(os.environ["COMMITTEES_OU"])

    directory.create(ou, autocreate_ou=True, ignore_existing=True)
    yield ou
    directory.delete(ou, ignore_nonexistent=True, recursive=True)


@pytest.fixture
def members_ou(directory: ActiveDirectoryClient) -> Generator[OrganizationalUnit, None, None]:
    ou = OrganizationalUnit(os.environ["MEMBERS_OU"])

    directory.create(ou, autocreate_ou=True, ignore_existing=True)
    yield ou
    directory.delete(ou, ignore_nonexistent=True, recursive=True)


@pytest.fixture
def member(directory: ActiveDirectoryClient, members_ou: OrganizationalUnit) -> Generator[ADUser, None, None]:
    member = ADUser(
        dn=f"CN=5678,{members_ou.get_dn()}",
        account_name="s1234567",
        first_name="Nathan",
        last_name="Emanuel",
        password="P@ssword2026!",
    )

    directory.create(member, ignore_existing=True)
    yield member
    directory.delete(member, ignore_nonexistent=True)


@pytest.fixture
def group(directory: ActiveDirectoryClient, committees_ou: OrganizationalUnit) -> Generator[ADGroup, None, None]:
    committee = ADGroup(
        dn=f"CN=12345,{committees_ou.get_dn()}",
        name="Test Committee",
        description="This is a test committee.",
        member_dns=set(),
    )

    directory.create(committee, ignore_existing=True)
    yield committee
    directory.delete(committee, ignore_nonexistent=True)


@pytest.fixture
def child_group(directory: ActiveDirectoryClient, committees_ou: OrganizationalUnit) -> Generator[ADGroup, None, None]:

    child_group = ADGroup(
        dn=f"CN=8967,{committees_ou.get_dn()}",
        name="Child group",
        description="This group is a member of another group",
        member_dns=set(),
    )

    directory.create(child_group, ignore_existing=True)
    yield child_group
    directory.delete(child_group, ignore_nonexistent=True)


@pytest.mark.integration
def test_connection(directory: ActiveDirectoryClient) -> None:
    assert directory.get_connection().bound


@pytest.mark.integration
def test_invalid_credentials() -> None:
    with pytest.raises(LDAPInvalidCredentialsResult):
        with ActiveDirectoryClient("invalid_dn", "invalid_pw") as ad:
            pass


@pytest.mark.integration
def test_create_delete_user(directory: ActiveDirectoryClient, members_ou: OrganizationalUnit) -> None:
    member = ADUser(
        dn=f"CN=5678,{members_ou.get_dn()}",
        account_name="s1234567",
        first_name="Nathan",
        last_name="Emanuel",
        password="P@ssword2026!",
    )

    try:
        directory.delete(member)
    except LDAPNoSuchObjectResult:
        pass

    with pytest.raises(LDAPNoSuchObjectResult):
        directory.delete(member)

    directory.create(member)
    with pytest.raises(AlreadyExistsException):
        directory.create(member)

    assert member.is_synced_in(directory)

    member.first_name = "First Name"
    member.last_name = "Last Name"
    assert not member.is_synced_in(directory)

    directory.delete(member)
    with pytest.raises(LDAPNoSuchObjectResult):
        directory.delete(member)


@pytest.mark.integration
def test_disable_user(directory: ActiveDirectoryClient, member: ADUser) -> None:
    member.disable_in(directory)
    member.disable_in(directory)


@pytest.mark.integration
def test_enable_user(directory: ActiveDirectoryClient, member: ADUser) -> None:
    member.disable_in(directory)
    member.enable_in(directory)
    member.enable_in(directory)
    member.disable_in(directory)
    member.enable_in(directory)
    member.disable_in(directory)


@pytest.mark.integration
def test_create_delete_group(directory: ActiveDirectoryClient, committees_ou: OrganizationalUnit) -> None:
    group = ADGroup(
        dn=f"CN=12345,{committees_ou.get_dn()}",
        name="Test Group",
        description="This is a test group.",
        member_dns=set(),
    )

    try:
        directory.delete(group)
    except LDAPNoSuchObjectResult:
        pass

    with pytest.raises(LDAPNoSuchObjectResult):
        directory.delete(group)

    directory.create(group)
    with pytest.raises(AlreadyExistsException):
        directory.create(group)

    assert group.is_synced_in(directory)

    group.name = "Updated Test Group"
    assert not group.is_synced_in(directory)

    directory.delete(group)
    with pytest.raises(LDAPNoSuchObjectResult):
        directory.delete(group)


@pytest.mark.integration
def test_add_to_remove_from_group(
    directory: ActiveDirectoryClient, member: ADUser, group: ADGroup, child_group: ADGroup
) -> None:

    with pytest.raises(LDAPNoSuchAttributeResult):
        group.remove_member_in(directory, member)

    group.add_member_in(directory, member)
    with pytest.raises(AlreadyExistsException):
        group.add_member_in(directory, member)

    group.add_member_in(directory, child_group)
    with pytest.raises(AlreadyExistsException):
        group.add_member_in(directory, child_group)

    assert group.is_synced_in(directory)

    group.remove_member_in(directory, child_group)
    with pytest.raises(LDAPUnwillingToPerformResult):
        group.remove_member_in(directory, child_group)

    group.remove_member_in(directory, member)
    with pytest.raises(LDAPUnwillingToPerformResult):
        group.remove_member_in(directory, member)


@pytest.mark.integration
def test_add_to_group_with_nonexistent_member(directory: ActiveDirectoryClient, group: ADGroup) -> None:
    fake_member = ADUser(
        dn=f"CN=9999,{group.ou}",
        account_name="s9999999",
        first_name="Fake",
        last_name="User",
        password="P@ssword2026!",
    )
    with pytest.raises(NoSuchGroupMemberException):
        group.add_member_in(directory, fake_member)
