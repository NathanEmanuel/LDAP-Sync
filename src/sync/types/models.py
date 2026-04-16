from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol


class Destination(Protocol):

    def create_group(self, group: DestinationGroup, ignore_existing: bool = False) -> bool: ...

    def create_user(self, user: DestinationUser, ignore_existing: bool = False) -> bool: ...

    def add_to_group(self, member: DestinationModel, group: DestinationGroup) -> None: ...


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

    def create_in(self, destination: Destination) -> None: ...


class SourceGroup(SourceModel):
    pass


class DestinationGroup(DestinationModel):

    @abstractmethod
    def add(self, member: DestinationModel, destination: Destination) -> None: ...


class SourceUser(SourceModel):
    pass


class DestinationUser(DestinationModel):
    pass
