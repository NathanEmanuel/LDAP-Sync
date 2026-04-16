from __future__ import annotations

from abc import ABC, abstractmethod
from types import TracebackType
from typing import Optional

from .models import DestinationGroup, DestinationModel, DestinationUser


class DestinationClient(ABC):

    @abstractmethod
    def create_group(self, group: DestinationGroup, ignore_existing: bool = False) -> bool: ...

    @abstractmethod
    def create_user(self, user: DestinationUser, ignore_existing: bool = False) -> bool: ...

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
