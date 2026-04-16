from abc import ABC, abstractmethod


class SyncableModel(ABC):

    @abstractmethod
    def get_id(self) -> str: ...
