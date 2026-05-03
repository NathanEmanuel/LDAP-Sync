from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence, Set
from contextlib import AbstractAsyncContextManager, AbstractContextManager
from typing import Generic, TypeVar, Union, overload

DESTINATION_DIR_TYPE = TypeVar("DESTINATION_DIR_TYPE", bound="DestinationDirectory")

DESTINATION_GROUP_TYPE = TypeVar("DESTINATION_GROUP_TYPE", bound="DestinationGroup")
DESTINATION_USER_TYPE = TypeVar("DESTINATION_USER_TYPE", bound="DestinationUser")
SOURCE_GROUP_TYPE = TypeVar("SOURCE_GROUP_TYPE", bound="SourceGroup")
SOURCE_USER_TYPE = TypeVar("SOURCE_USER_TYPE", bound="SourceUser")


class DestinationDirectory(AbstractContextManager, ABC):
    pass


class SourceDirectory(AbstractAsyncContextManager, ABC, Generic[SOURCE_GROUP_TYPE, SOURCE_USER_TYPE]):

    @abstractmethod
    async def get_groups(self) -> Sequence[SOURCE_GROUP_TYPE]: ...


class DirectoryMapper(
    ABC, Generic[SOURCE_GROUP_TYPE, SOURCE_USER_TYPE, DESTINATION_DIR_TYPE, DESTINATION_GROUP_TYPE, DESTINATION_USER_TYPE]
):

    @overload
    def convert(
        self, principal: SourceGroup[SOURCE_GROUP_TYPE, SOURCE_USER_TYPE]
    ) -> DestinationGroup[DESTINATION_DIR_TYPE, DESTINATION_GROUP_TYPE, DESTINATION_USER_TYPE]: ...

    @overload
    def convert(self, principal: SOURCE_USER_TYPE) -> DestinationUser[DESTINATION_DIR_TYPE]: ...

    @abstractmethod
    def convert(self, principal: Union[SourceGroup[SOURCE_GROUP_TYPE, SOURCE_USER_TYPE], SOURCE_USER_TYPE]) -> Union[
        DestinationGroup[DESTINATION_DIR_TYPE, DESTINATION_GROUP_TYPE, DESTINATION_USER_TYPE],
        DestinationUser[DESTINATION_DIR_TYPE],
    ]: ...


class Syncable(ABC):

    @abstractmethod
    def get_id(self) -> str: ...

    @abstractmethod
    def get_name(self) -> str: ...


class SourcePrincipal(Syncable):
    pass


class DestinationPrincipal(Syncable, Generic[DESTINATION_DIR_TYPE]):

    @abstractmethod
    def is_synced_in(self, directory: DESTINATION_DIR_TYPE) -> bool: ...

    @abstractmethod
    def fetch_in(self, directory: DESTINATION_DIR_TYPE) -> DestinationPrincipal[DESTINATION_DIR_TYPE]: ...

    @abstractmethod
    def create_in(self, directory: DESTINATION_DIR_TYPE) -> None: ...


class SourceGroup(SourcePrincipal, Generic[SOURCE_GROUP_TYPE, SOURCE_USER_TYPE]):

    @abstractmethod
    def get_members(self) -> Set[Union[SOURCE_GROUP_TYPE, SOURCE_USER_TYPE]]: ...


class DestinationGroup(
    DestinationPrincipal[DESTINATION_DIR_TYPE], Generic[DESTINATION_DIR_TYPE, DESTINATION_GROUP_TYPE, DESTINATION_USER_TYPE]
):

    @abstractmethod
    def add_member_in(
        self, directory: DESTINATION_DIR_TYPE, member: Union[DESTINATION_GROUP_TYPE, DESTINATION_USER_TYPE]
    ) -> None: ...


class SourceUser(SourcePrincipal):
    pass


class DestinationUser(DestinationPrincipal[DESTINATION_DIR_TYPE], Generic[DESTINATION_DIR_TYPE]):
    pass
