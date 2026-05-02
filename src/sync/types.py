from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence, Set
from types import TracebackType
from typing import Generic, Optional, TypeVar, Union

DESTINATION_TYPE = TypeVar("DESTINATION_TYPE", bound="DestinationClient")

DESTINATION_GROUP_TYPE = TypeVar("DESTINATION_GROUP_TYPE", bound="DestinationGroup")
DESTINATION_USER_TYPE = TypeVar("DESTINATION_USER_TYPE", bound="DestinationUser")
SOURCE_GROUP_TYPE = TypeVar("SOURCE_GROUP_TYPE", bound="SourceGroup")
SOURCE_USER_TYPE = TypeVar("SOURCE_USER_TYPE", bound="SourceUser")


class DestinationClient(ABC):

    @abstractmethod
    def is_synced(self, entry: DestinationModel) -> bool: ...

    @abstractmethod
    def create_group(self, group: DestinationGroup) -> None: ...

    @abstractmethod
    def create_user(self, user: DestinationUser) -> None: ...

    @abstractmethod
    def add_to_group(self, member: DestinationModel, group: DestinationGroup) -> None: ...

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


class ModelConverter(ABC):

    @abstractmethod
    def convert_group(self, group: SourceGroup) -> DestinationGroup: ...

    @abstractmethod
    def convert_user(self, user: SourceUser) -> DestinationUser: ...


class Syncable(ABC):

    @abstractmethod
    def get_id(self) -> str: ...

    @abstractmethod
    def get_name(self) -> str: ...


class SourceModel(Syncable):

    @abstractmethod
    def convert_with(self, model_converter: ModelConverter) -> DestinationModel: ...


class DestinationModel(Syncable):

    @abstractmethod
    def create_in(self, destination: DestinationClient) -> None: ...


class SourceGroup(SourceModel):
    pass


class DestinationGroup(DestinationModel):

    @abstractmethod
    def add(self, member: DestinationModel, destination: DestinationClient) -> None: ...


class SourceUser(SourceModel):
    pass


class DestinationUser(DestinationModel):
    pass
