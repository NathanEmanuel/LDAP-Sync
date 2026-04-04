from __future__ import annotations

import argparse
import asyncio
import inspect
import json
import os
import sys
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from dotenv import load_dotenv

from congressus.client import Client
from ldap.ldap import Ldap, LdapConnectionError

T = TypeVar("T")


def _require_env(*keys: str) -> dict[str, str]:
    values: dict[str, str] = {}
    missing: list[str] = []

    for key in keys:
        value = os.getenv(key)
        if value is None or value == "":
            missing.append(key)
        else:
            values[key] = value

    if missing:
        joined = ", ".join(missing)
        raise SystemExit(f"Missing required environment variable(s): {joined}")

    return values


def _print_json(data: Any) -> None:
    print(json.dumps(data, indent=2))


async def _run_with_spinner(message: str, operation: Callable[[], Awaitable[T]]) -> T:
    stop = asyncio.Event()

    async def spin() -> None:
        frames = "|/-\\"
        index = 0
        while not stop.is_set():
            frame = frames[index % len(frames)]
            sys.stderr.write(f"\r{message} {frame}")
            sys.stderr.flush()
            index += 1
            try:
                await asyncio.wait_for(stop.wait(), timeout=0.1)
            except TimeoutError:
                continue

        sys.stderr.write("\r" + (" " * (len(message) + 2)) + "\r")
        sys.stderr.flush()

    spinner_task = asyncio.create_task(spin())
    try:
        return await operation()
    finally:
        stop.set()
        await spinner_task


async def _with_congressus_client(operation: Callable[[Client], Awaitable[T]]) -> T:
    env = _require_env("CONGRESSUS_API_KEY")
    base_url = os.getenv("CONGRESSUS_API_BASE_URL", "https://api.congressus.nl/v30")

    async with Client(base_url=base_url, api_key=env["CONGRESSUS_API_KEY"]) as client:
        return await operation(client)


async def _congressus_list_committees(args: argparse.Namespace) -> int:
    if args.ended and args.committee_kind is None:
        raise SystemExit("--ended requires either --standing/-s or --annual/-a")

    async def operation(client: Client):
        match args.committee_kind:
            case "annual":
                return (
                    await client.list_annual_committees(page=args.page)
                    if args.ended
                    else await client.list_active_annual_committees()
                )
            case "standing":
                return (
                    await client.list_standing_committees(page=args.page)
                    if args.ended
                    else await client.list_active_standing_committees()
                )
            case _:
                return (await client.list_active_committees())

    groups = await _run_with_spinner("Fetching...", lambda: _with_congressus_client(operation))
    if groups is None:
        print("No committees found.")
        return 0

    if args.json:
        _print_json([group.model_dump(mode="json") for group in groups])
        return 0

    for group in groups:
        print(f"{group.id}\t{group.name}")
    return 0


async def _congressus_get_group(args: argparse.Namespace) -> int:
    group = await _with_congressus_client(lambda client: client.retrieve_group(args.group_id))

    _print_json(group.model_dump(mode="json"))
    return 0


async def _congressus_get_member(args: argparse.Namespace) -> int:
    member = await _with_congressus_client(lambda client: client.retrieve_member(args.member_id))

    _print_json(member.model_dump(mode="json"))
    return 0


async def _congressus_list_memberships(args: argparse.Namespace) -> int:
    memberships = await _with_congressus_client(
        lambda client: client.list_group_memberships(group_id=args.group_id, member_id=args.member_id)
    )

    _print_json([membership.model_dump(mode="json") for membership in memberships])
    return 0


def _ldap_check_bind(_: argparse.Namespace) -> int:
    env = _require_env("ADMIN_DN", "ADMIN_PW")
    try:
        with Ldap(env["ADMIN_DN"], env["ADMIN_PW"]):
            print("LDAP bind succeeded.")
    except LdapConnectionError as exc:
        print(f"LDAP bind failed: {exc}")
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ldap-sync",
        description="Command-line utilities for Congressus and LDAP sync operations.",
    )
    subparsers = parser.add_subparsers(dest="service", required=True)

    congressus = subparsers.add_parser("congressus", help="Query Congressus API")
    congressus_sub = congressus.add_subparsers(dest="command", required=True)

    committees = congressus_sub.add_parser("committees", help="List committees")
    committee_kind = committees.add_mutually_exclusive_group()
    committee_kind.add_argument("--standing", "-s", dest="committee_kind", action="store_const", const="standing")
    committee_kind.add_argument("--annual", "-a", dest="committee_kind", action="store_const", const="annual")
    committees.add_argument("--ended", action="store_true", help="Also show ended committees (requires -s or -a)")
    committees.add_argument("--json", action="store_true", help="Output JSON")
    committees.add_argument("-p", "--page", type=int, default=1, help="Page number for pagination")
    committees.set_defaults(handler=_congressus_list_committees)

    group = congressus_sub.add_parser("group", help="Retrieve one group by ID")
    group.add_argument("group_id", type=int)
    group.set_defaults(handler=_congressus_get_group)

    member = congressus_sub.add_parser("member", help="Retrieve one member by ID")
    member.add_argument("member_id", type=int)
    member.set_defaults(handler=_congressus_get_member)

    memberships = congressus_sub.add_parser("memberships", help="List memberships")
    memberships.add_argument("--group-id", action="append", type=int, default=[], help="Filter by group ID")
    memberships.add_argument("--member-id", action="append", type=int, default=[], help="Filter by member ID")
    memberships.set_defaults(handler=_congressus_list_memberships)

    ldap = subparsers.add_parser("ldap", help="LDAP operations")
    ldap_sub = ldap.add_subparsers(dest="command", required=True)

    check_bind = ldap_sub.add_parser("check-bind", help="Test LDAP bind using ADMIN_DN and ADMIN_PW")
    check_bind.set_defaults(handler=_ldap_check_bind)

    return parser


def main() -> int:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args()

    handler = args.handler
    if inspect.iscoroutinefunction(handler):
        return asyncio.run(handler(args))
    return handler(args)
