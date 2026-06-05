from uuid import UUID
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models.usage import Usage


class UsageRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_usage(
        self,
        agent_id: UUID,
        credits_used: float,
        usage_type: str,
        wallet_id: Optional[UUID] = None,
        workflow_execution_id: Optional[UUID] = None,
        description: Optional[str] = None,
        usage_metadata: Optional[dict] = None
    ) -> Usage:
        usage = Usage(
            agent_id=agent_id,
            wallet_id=wallet_id,
            workflow_execution_id=workflow_execution_id,
            credits_used=credits_used,
            usage_type=usage_type,
            description=description,
            usage_metadata=usage_metadata
        )
        self.db.add(usage)
        self.db.commit()
        self.db.refresh(usage)
        return usage

    def get_by_id(self, usage_id: UUID) -> Optional[Usage]:
        return self.db.query(Usage).filter(Usage.id == usage_id).first()

    def get_by_agent(
        self,
        agent_id: UUID,
        skip: int = 0,
        limit: int = 100,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> list[Usage]:
        query = self.db.query(Usage).filter(Usage.agent_id == agent_id)
        
        if start_date:
            query = query.filter(Usage.created_at >= start_date)
        if end_date:
            query = query.filter(Usage.created_at <= end_date)
        
        return (
            query
            .order_by(Usage.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_wallet(
        self,
        wallet_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> list[Usage]:
        return (
            self.db.query(Usage)
            .filter(Usage.wallet_id == wallet_id)
            .order_by(Usage.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_workflow_execution(
        self,
        workflow_execution_id: UUID
    ) -> Optional[Usage]:
        return (
            self.db.query(Usage)
            .filter(Usage.workflow_execution_id == workflow_execution_id)
            .first()
        )

    def get_total_credits_used(
        self,
        agent_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> float:
        query = self.db.query(func.sum(Usage.credits_used)).filter(
            Usage.agent_id == agent_id
        )
        
        if start_date:
            query = query.filter(Usage.created_at >= start_date)
        if end_date:
            query = query.filter(Usage.created_at <= end_date)
        
        total = query.scalar()
        return float(total) if total else 0.0

    def get_usage_by_type(
        self,
        agent_id: UUID,
        usage_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> float:
        query = self.db.query(func.sum(Usage.credits_used)).filter(
            and_(
                Usage.agent_id == agent_id,
                Usage.usage_type == usage_type
            )
        )
        
        if start_date:
            query = query.filter(Usage.created_at >= start_date)
        if end_date:
            query = query.filter(Usage.created_at <= end_date)
        
        total = query.scalar()
        return float(total) if total else 0.0

    def get_recent_usage(
        self,
        agent_id: Optional[UUID] = None,
        limit: int = 20
    ) -> list[Usage]:
        query = self.db.query(Usage)
        if agent_id:
            query = query.filter(Usage.agent_id == agent_id)
        return (
            query
            .order_by(Usage.created_at.desc())
            .limit(limit)
            .all()
        )

    def delete_usage(self, usage_id: UUID) -> bool:
        usage = self.get_by_id(usage_id)
        if usage:
            self.db.delete(usage)
            self.db.commit()
            return True
        return False

    def get_usage_summary_by_type(
        self,
        agent_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> list[dict]:
        query = self.db.query(
            Usage.usage_type,
            func.sum(Usage.credits_used).label('total_credits'),
            func.count(Usage.id).label('usage_count')
        ).filter(Usage.agent_id == agent_id)
        
        if start_date:
            query = query.filter(Usage.created_at >= start_date)
        if end_date:
            query = query.filter(Usage.created_at <= end_date)
        
        results = query.group_by(Usage.usage_type).all()
        
        return [
            {
                'usage_type': r[0],
                'total_credits': float(r[1]) if r[1] else 0.0,
                'usage_count': r[2]
            }
            for r in results
        ]

    def get_daily_usage(
        self,
        agent_id: UUID,
        days: int = 30
    ) -> list[dict]:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        results = (
            self.db.query(
                func.date(Usage.created_at).label('date'),
                func.sum(Usage.credits_used).label('total_credits')
            )
            .filter(
                and_(
                    Usage.agent_id == agent_id,
                    Usage.created_at >= start_date
                )
            )
            .group_by(func.date(Usage.created_at))
            .order_by(func.date(Usage.created_at).desc())
            .all()
        )
        
        return [
            {
                'date': r[0],
                'total_credits': float(r[1]) if r[1] else 0.0
            }
            for r in results
        ]