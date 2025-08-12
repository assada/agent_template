from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session

from .connection import DatabaseConnection
from .session import SessionManager


class SQLModelManager(SessionManager):
    def __init__(self, db_connection: DatabaseConnection):
        self._db_connection = db_connection
        self._engine: Engine | None = None
        self._session_factory: sessionmaker[Session] | None = None

    def _get_engine(self) -> Engine:
        if self._engine is None:
            self._engine = create_engine(
                self._db_connection.get_connection_string().replace(
                    "postgresql://", "postgresql+psycopg://"
                ),
                pool_pre_ping=True,
                pool_recycle=3600,
                pool_size=10,
                max_overflow=20,
                pool_timeout=30,
            )
        return self._engine

    def _get_session_factory(self) -> sessionmaker[Session]:
        if self._session_factory is None:
            engine = self._get_engine()
            self._session_factory = sessionmaker(
                engine, class_=Session, expire_on_commit=False
            )
        return self._session_factory

    def get_session(self) -> Session:
        session_factory = self._get_session_factory()
        return session_factory()
