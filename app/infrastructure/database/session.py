from abc import ABC, abstractmethod

from sqlmodel import Session


class SessionManager(ABC):
    @abstractmethod
    def get_session(self) -> Session:
        pass
