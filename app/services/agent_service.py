from uuid import UUID

from app.models.agents import Agent
from app.repositories.agent_repository import AgentRepository


class AgentLimitExceededError(Exception):
    pass


class AgentAlreadyExistsError(Exception):
    pass


class AgentService:
    def __init__(self, agent_repo: AgentRepository):
        self.agent_repo = agent_repo

    def create_agent(
        self,
        user_id: UUID,
        name: str,
        description: str | None = None
    ) -> Agent:
        if self.agent_repo.agent_name_exists(user_id, name):
            raise AgentAlreadyExistsError(
                f"Agent '{name}' already exists"
            )

        agent_count = self.agent_repo.count_by_user(user_id)

        if agent_count >= 3:
            raise AgentLimitExceededError(
                f"User {user_id} cannot create more than 3 agents. Current count: {agent_count}"
            )

        return self.agent_repo.create_agent(
            user_id=user_id,
            name=name,
            description=description
        )

    def get_user_agents(self, user_id: UUID) -> list[Agent]:
        return self.agent_repo.get_by_user(user_id)

    def get_agent(self, agent_id: UUID) -> Agent | None:
        return self.agent_repo.get_by_id(agent_id)

    def delete_agent(self, agent_id: UUID) -> bool:
        return self.agent_repo.delete_agent(agent_id)