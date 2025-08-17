from typing import Any

from dependency_injector import containers, providers
from langfuse import Langfuse
from sqlmodel import Session

from app.bootstrap.config import get_config

from .agent.langgraph.checkpoint.memory import MemoryCheckpointer
from .agent.langgraph.checkpoint.postgres import PostgresCheckpointer
from .agent.langgraph.checkpoint.resolver import CheckpointerResolver
from .infrastructure import DatabaseConnection
from .infrastructure.database import PostgreSQLConnection, SQLModelManager
from .infrastructure.database.session import SessionManager


def create_checkpointer_resolver(
        memory_checkpointer: MemoryCheckpointer,
        postgres_checkpointer: PostgresCheckpointer,
) -> CheckpointerResolver:
    return CheckpointerResolver(
        memory_checkpointer=memory_checkpointer,
        postgres_checkpointer=postgres_checkpointer,
    )


def create_session(sqlmodel_manager: SQLModelManager) -> Session:
    return sqlmodel_manager.get_session()


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=[
            "app.http.routes.thread_routes",
            "app.http.routes.runs_routes",
            "app.http.middleware",
            "app.http.controllers",
            "app.agent.factory",
        ]
    )

    config = providers.Singleton(get_config)

    db_connection: providers.Singleton[DatabaseConnection] = providers.Singleton(PostgreSQLConnection, config=config)
    sqlmodel_manager: providers.Singleton[SessionManager] = providers.Singleton(
        SQLModelManager,
        db_connection=db_connection
    )

    user_repository: providers.Factory[Any] = providers.Factory(
        "app.repositories.UserRepository",
        session_manager=sqlmodel_manager,
    )
    thread_repository: providers.Factory[Any] = providers.Factory(
        "app.repositories.ThreadRepository",
        session_manager=sqlmodel_manager,
    )

    thread_service: providers.Factory[Any] = providers.Factory(
        "app.services.thread_service.ThreadService", thread_repository=thread_repository
    )
    user_service: providers.Factory[Any] = providers.Factory(
        "app.services.user_service.UserService", user_repository=user_repository
    )

    memory_checkpointer: providers.Singleton[Any] = providers.Singleton(
        "app.agent.langgraph.checkpoint.memory.MemoryCheckpointer"
    )
    postgres_checkpointer: providers.Singleton[Any] = providers.Singleton(
        "app.agent.langgraph.checkpoint.postgres.PostgresCheckpointer",
        database_connection=db_connection,
    )

    checkpointer_resolver: providers.Singleton[Any] = providers.Singleton(
        create_checkpointer_resolver,
        memory_checkpointer=memory_checkpointer,
        postgres_checkpointer=postgres_checkpointer,
    )

    langfuse_client: providers.Singleton[Any] = providers.Singleton(
        Langfuse,
        debug=False,
    )

    prompt_provider_resolver: providers.Singleton[Any] = providers.Singleton(
        "app.agent.prompt_resolver.PromptProviderResolver",
        config=config,
        langfuse_client=langfuse_client,
    )

    agent_factory: providers.Singleton[Any] = providers.Singleton(
        "app.agent.factory.AgentFactory",
        global_config=config,
        langfuse_client=langfuse_client,
        checkpointer_resolver=checkpointer_resolver,
        prompt_provider_resolver=prompt_provider_resolver,
    )

    agent_service: providers.Singleton[Any] = providers.Singleton(
        "app.agent.services.AgentService",
        langfuse_client=langfuse_client,
    )

    thread_controller: providers.Singleton[Any] = providers.Singleton(
        "app.http.controllers.ThreadController",
        config=config,
        agent_factory=agent_factory,
        agent_service=agent_service,
        thread_service=thread_service,
    )
