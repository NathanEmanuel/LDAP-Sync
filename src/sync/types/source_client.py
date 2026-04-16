from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Sequence
from types import TracebackType
from typing import Optional

from .models import SourceGroup, SourceModel


class SourceClient(ABC):

    @abstractmethod
    async def get_groups(self) -> Sequence[SourceGroup]: ...

    @abstractmethod
    async def get_group_members(self, group: SourceGroup) -> AsyncIterator[SourceModel]: ...

    @abstractmethod
    async def __aenter__(self) -> SourceClient: ...

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> Optional[bool]: ...
