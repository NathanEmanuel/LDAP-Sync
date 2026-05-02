from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence, Set
from types import TracebackType
from typing import Generic, Optional, TypeVar, Union, overload

DESTINATION_TYPE = TypeVar("DESTINATION_TYPE", bound="DestinationClient")

DESTINATION_GROUP_TYPE = TypeVar("DESTINATION_GROUP_TYPE", bound="DestinationGroup")
DESTINATION_USER_TYPE = TypeVar("DESTINATION_USER_TYPE", bound="DestinationUser")
SOURCE_GROUP_TYPE = TypeVar("SOURCE_GROUP_TYPE", bound="SourceGroup")
SOURCE_USER_TYPE = TypeVar("SOURCE_USER_TYPE", bound="SourceUser")


class DestinationClient(ABC):

    @abstractmethod
    def __enter__(self) -> DestinationClient: ...

    @abstractmethod
    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> Optional[bool]: ...


class SourceClient(ABC, Generic[SOURCE_GROUP_TYPE, SOURCE_USER_TYPE]):

    @abstractmethod
    async def get_groups(self) -> Sequence[SOURCE_GROUP_TYPE]: ...

    @abstractmethod
    async def __aenter__(self) -> SourceClient[SOURCE_GROUP_TYPE, SOURCE_USER_TYPE]: ...

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> Optional[bool]: ...


class ModelConverter(
    ABC, Generic[SOURCE_GROUP_TYPE, SOURCE_USER_TYPE, DESTINATION_TYPE, DESTINATION_GROUP_TYPE, DESTINATION_USER_TYPE]
):

    @overload
    def convert(
        self, entry: SourceGroup[SOURCE_GROUP_TYPE, SOURCE_USER_TYPE]
    ) -> DestinationGroup[DESTINATION_TYPE, DESTINATION_GROUP_TYPE, DESTINATION_USER_TYPE]: ...

    @overload
    def convert(self, entry: SOURCE_USER_TYPE) -> DestinationUser[DESTINATION_TYPE]: ...

    @abstractmethod
    def convert(
        self, entry: Union[SourceGroup[SOURCE_GROUP_TYPE, SOURCE_USER_TYPE], SOURCE_USER_TYPE]
    ) -> Union[
        DestinationGroup[DESTINATION_TYPE, DESTINATION_GROUP_TYPE, DESTINATION_USER_TYPE], DestinationUser[DESTINATION_TYPE]
    ]: ...


class Syncable(ABC):

    @abstractmethod
    def get_id(self) -> str: ...

    @abstractmethod
    def get_name(self) -> str: ...


class SourceModel(Syncable):
    pass


class DestinationModel(Syncable, Generic[DESTINATION_TYPE]):

    @abstractmethod
    def is_synced_in(self, destination: DESTINATION_TYPE) -> bool: ...

    @abstractmethod
    def fetch_in(self, destination: DESTINATION_TYPE) -> DestinationModel[DESTINATION_TYPE]: ...

    @abstractmethod
    def create_in(self, destination: DESTINATION_TYPE) -> None: ...


class SourceGroup(SourceModel, Generic[SOURCE_GROUP_TYPE, SOURCE_USER_TYPE]):

    @abstractmethod
    def get_members(self) -> Set[Union[SOURCE_GROUP_TYPE, SOURCE_USER_TYPE]]: ...


class DestinationGroup(
    DestinationModel[DESTINATION_TYPE], Generic[DESTINATION_TYPE, DESTINATION_GROUP_TYPE, DESTINATION_USER_TYPE]
):

    @abstractmethod
    def add_member_in(
        self, directory: DESTINATION_TYPE, member: Union[DESTINATION_GROUP_TYPE, DESTINATION_USER_TYPE]
    ) -> None: ...


class SourceUser(SourceModel):
    pass


class DestinationUser(DestinationModel[DESTINATION_TYPE], Generic[DESTINATION_TYPE]):
    pass
