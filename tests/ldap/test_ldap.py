import os
from collections.abc import Generator

import pytest

from ldap.ldap import Ldap, LdapConnectionError
from ldap.models.group import Group
from ldap.models.user import User


@pytest.fixture
def ldap() -> Generator[Ldap, None, None]:
    with Ldap(os.environ["ADMIN_DN"], os.environ["ADMIN_PW"]) as ldap:
        yield ldap

@pytest.mark.integration
def test_ldap_connection(ldap: Ldap) -> None:
    assert ldap.get_ldap_connection().bound

@pytest.mark.integration
def test_ldap_invalid_credentials() -> None:
    with pytest.raises(LdapConnectionError):
        with Ldap("invalid_dn", "invalid_pw") as ldap:
            pass

@pytest.mark.integration
def test_create_user(ldap: Ldap, member: User) -> None:
    ldap.create_user(member)
    ldap.delete_user(member.dn)

@pytest.mark.integration
def test_disable_user(ldap: Ldap, member: User) -> None:
    ldap.create_user(member)
    ldap.disable_user(member.dn)
    ldap.delete_user(member.dn)

@pytest.mark.integration
def test_enable_user(ldap: Ldap, member: User) -> None:
    ldap.create_user(member)
    ldap.disable_user(member.dn)
    ldap.enable_user(member.dn)
    ldap.delete_user(member.dn)

@pytest.mark.integration
def test_create_group(ldap: Ldap, committee: Group) -> None:
    ldap.create_group(committee)
    ldap.delete_group(committee.dn)

@pytest.mark.integration
def test_add_to_group(ldap: Ldap, member: User, committee: Group) -> None:
    ldap.create_user(member)
    ldap.create_group(committee)
    ldap.add_to_group(member.dn, committee.dn)
    ldap.delete_group(committee.dn)
    ldap.delete_user(member.dn)

@pytest.mark.integration
def test_delete_group(ldap: Ldap, committee: Group) -> None:
    ldap.create_group(committee)
    ldap.delete_group(committee.dn)
    with pytest.raises(LdapConnectionError):
        ldap.delete_group(committee.dn)

@pytest.mark.integration
def test_delete_user(ldap: Ldap, member: User) -> None:
    ldap.create_user(member)
    ldap.delete_user(member.dn)
    with pytest.raises(LdapConnectionError):
        ldap.delete_user(member.dn)
