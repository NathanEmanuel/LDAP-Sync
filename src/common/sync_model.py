from abc import ABC, abstractmethod


class SyncModel(ABC):

    @abstractmethod
    def get_id(self) -> str: ...
