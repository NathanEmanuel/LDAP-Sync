import argparse
import asyncio
import inspect
import sys
from dataclasses import dataclass
from typing import Any, TypeVar

from ldap3.core.exceptions import LDAPBindError

from congressus import CongressusClient
from ldap import LdapClient
from sync import AccountSyncer
from sync.factories import LdapModelFactory

T = TypeVar("T")


@dataclass
class Env:
    CONGRESSUS_API_BASE_URL: str
    CONGRESSUS_API_KEY: str
    CONGRESSUS_API_COMMITTEE_FOLDER_ID: str
    ADMIN_DN: str
    ADMIN_PW: str
    BASE_OU: str
    MEMBERS_OU: str


class Cli:
    """
    Command-line interface for interacting with Congressus API and LDAP sync operations.
    """

    def __init__(self, env: Env):

        base_url = env.CONGRESSUS_API_BASE_URL
        api_key = env.CONGRESSUS_API_KEY
        committee_folder_id = int(env.CONGRESSUS_API_COMMITTEE_FOLDER_ID)
        ldap_model_factory = LdapModelFactory(base_ou=env.BASE_OU, member_ou=env.MEMBERS_OU)

        self._congressus_client = CongressusClient(base_url, api_key, committee_folder_id)
        self._ldap_client = LdapClient(env.ADMIN_DN, env.ADMIN_PW)
        self._sync = AccountSyncer(self._congressus_client, self._ldap_client, ldap_model_factory)

        # Bug in CPython <3.12 on Windows
        if sys.platform == "win32" and sys.version_info < (3, 12):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    def run(self) -> Any:
        parser = self._build_parser()
        args = parser.parse_args()
        handler = args.handler

        if inspect.iscoroutinefunction(handler):
            return asyncio.run(handler(args))

        return handler(args)

    def _build_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            prog="ldap-sync",
            description="Command-line utilities for Congressus and LDAP sync operations.",
        )
        subparsers = parser.add_subparsers(dest="service", required=True)

        sync = subparsers.add_parser("sync", help="Sync Congressus groups to the Directory")
        sync.add_argument(
            "--dry-run", "-d", action="store_true", help="Perform a dry run without making changes to the Directory"
        )
        sync.add_argument("--group-ids", "-g", nargs="+", type=int, help="Sync given groups (default: all)")
        sync.set_defaults(handler=self._congressus_sync)

        congressus = subparsers.add_parser("congressus", help="Query Congressus API")
        congressus_sub = congressus.add_subparsers(dest="command", required=True)

        active_members = congressus_sub.add_parser("active-members", help="List active members")
        active_members.add_argument("--json", action="store_true", help="Output JSON")
        active_members.add_argument("-p", "--page", type=int, default=1, help="Page number for pagination")
        active_members.set_defaults(handler=self._congressus_list_active_members)

        ldap = subparsers.add_parser("ldap", help="LDAP operations")
        ldap_sub = ldap.add_subparsers(dest="command", required=True)

        check_bind = ldap_sub.add_parser("check-bind", help="Test LDAP bind using ADMIN_DN and ADMIN_PW")
        check_bind.set_defaults(handler=self._ldap_check_bind)

        return parser

    async def _congressus_sync(self, args: argparse.Namespace) -> int:
        with self._sync:
            if args.group_ids:
                await self._sync._sync_groups(args.group_ids, args.dry_run)
            else:
                await self._sync.sync_all(args.dry_run)

        return 0

    async def _congressus_list_active_members(self, args: argparse.Namespace) -> int:
        async for m in self._congressus_client.list_active_members():
            print(f"{m.id}\t{m.first_name} {m.last_name}")

        return 0

    async def _ldap_check_bind(self, args: argparse.Namespace) -> int:
        try:
            with self._ldap_client:
                print("LDAP bind succeeded.")
        except LDAPBindError as e:
            print(f"LDAP bind failed: {e}")
            return 1
        return 0
