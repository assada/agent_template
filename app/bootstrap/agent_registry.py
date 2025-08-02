from app.agent.config import AgentConfig
from app.agent.factory import AgentFactory


def register_agents() -> None:
    AgentFactory.register_agent(
        agent_id="demo_agent",
        agent_class_path="app.agent.langgraph.demo.demo_agent.DemoAgent",
        config=AgentConfig(
            prompt_source="langfuse",
            custom_params={
                "max_iterations": 10,
                "temperature": 0.7,
            },
        ),
    )

    # Example production agent
    # AgentFactory.register_agent(
    #     agent_id="demo_agent_prod",
    #     agent_class_path="app.agent.langgraph.demo.demo_agent.DemoAgent",
    #     config=AgentConfig(
    #         prompt_source="langfuse",
    #         custom_params={
    #             "max_iterations": 15,
    #             "temperature": 0.5,
    #         }
    #     )
    # )


def validate_agent_id(agent_id: str | None) -> str:
    if agent_id is None:
        raise ValueError("Agent ID is required")

    available_agents = AgentFactory.list_agents()
    if agent_id not in available_agents:
        raise ValueError(
            f"Agent '{agent_id}' not found. Available agents: {available_agents}"
        )

    return agent_id
