from collections.abc import AsyncGenerator, Generator
import os

import pytest

from directories.active_directory.active_directory_client import ActiveDirectoryClient, ADEntry
from directories.active_directory.schemas import OrganizationalUnit
from directories.congressus.congressus_client import CongressusClient
from directory_converters.congressus_to_active_directory_mapper import CongressusToActiveDirectoryMapper
from sync.principal_syncer import PrincipalSyncer
from sync.types import DestinationDirectory, SourceDirectory


@pytest.fixture
async def source_directory() -> AsyncGenerator[SourceDirectory, None]:
    async with CongressusClient(
        os.environ["CONGRESSUS_API_BASE_URL"],
        os.environ["CONGRESSUS_API_KEY"],
        int(os.environ["CONGRESSUS_API_COMMITTEE_FOLDER_ID"]),
    ) as client:
        yield client


@pytest.fixture
def destination_directory() -> Generator[DestinationDirectory, None, None]:
    directory = ActiveDirectoryClient(
        os.environ["ADMIN_DN"],
        os.environ["ADMIN_PW"],
    )

    base_ou = OrganizationalUnit(os.environ["BASE_OU"])

    with directory:
        directory.delete(base_ou, ignore_nonexistent=True, recursive=True)
        yield directory


@pytest.fixture
def directory_mapper() -> Generator[CongressusToActiveDirectoryMapper, None, None]:
    yield CongressusToActiveDirectoryMapper(
        os.environ["BASE_OU"],
        os.environ["MEMBERS_OU"],
    )


@pytest.fixture
def syncer(source_directory, destination_directory, directory_mapper) -> Generator[PrincipalSyncer, None, None]:
    yield PrincipalSyncer(
        source_directory=source_directory,
        destination_directory=destination_directory,
        directory_mapper=directory_mapper,
    )


@pytest.mark.system
async def test_sync_all(syncer: PrincipalSyncer) -> None:
    await syncer.sync_all()
