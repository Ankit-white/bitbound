from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.agents import Agent


class AgentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_agent(
        self,
        user_id: UUID,
        name: str,
        description: str | None = None
    ) -> Agent:
        agent = Agent(
            user_id=user_id,
            name=name,
            description=description
        )
        self.db.add(agent)
        self.db.commit()
        self.db.refresh(agent)
        return agent

    def get_by_id(self, agent_id: UUID) -> Agent | None:
        return self.db.query(Agent).filter(Agent.id == agent_id).first()

    def get_by_user(self, user_id: UUID) -> list[Agent]:
        return (
            self.db.query(Agent)
            .filter(Agent.user_id == user_id)
            .order_by(Agent.created_at.desc())
            .all()
        )

    def count_by_user(self, user_id: UUID) -> int:
        return (
            self.db.query(func.count(Agent.id))
            .filter(Agent.user_id == user_id)
            .scalar()
            or 0
        )

    def delete_agent(self, agent_id: UUID) -> bool:
        agent = self.get_by_id(agent_id)
        if not agent:
            return False
        self.db.delete(agent)
        self.db.commit()
        return True

    def agent_name_exists(self, user_id: UUID, name: str) -> bool:
        return (
            self.db.query(Agent)
            .filter(
                Agent.user_id == user_id,
                Agent.name == name
            )
            .first()
            is not None
        )