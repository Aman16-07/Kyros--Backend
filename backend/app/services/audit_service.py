"""Audit Service for logging all system changes."""

from typing import Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditAction, AuditLog


class AuditService:
    """
    Service for creating audit log entries.
    
    Usage:
        audit = AuditService(db)
        await audit.log_create("SeasonPlan", plan.id, user_id, new_data=plan_dict)
        await audit.log_update("SeasonPlan", plan.id, user_id, old_data, new_data)
        await audit.log_delete("SeasonPlan", plan.id, user_id, old_data=plan_dict)
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def log(
        self,
        entity_type: str,
        entity_id: UUID,
        action: AuditAction,
        user_id: Optional[UUID] = None,
        old_data: Optional[dict[str, Any]] = None,
        new_data: Optional[dict[str, Any]] = None,
        description: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        season_id: Optional[UUID] = None,
    ) -> AuditLog:
        """Create an audit log entry."""
        log_entry = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            user_id=user_id,
            old_data=old_data,
            new_data=new_data,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            season_id=season_id,
        )
        self.session.add(log_entry)
        await self.session.flush()
        return log_entry
    
    async def log_create(
        self,
        entity_type: str,
        entity_id: UUID,
        user_id: Optional[UUID] = None,
        new_data: Optional[dict[str, Any]] = None,
        description: Optional[str] = None,
        season_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """Log a create action."""
        return await self.log(
            entity_type=entity_type,
            entity_id=entity_id,
            action=AuditAction.CREATE,
            user_id=user_id,
            new_data=new_data,
            description=description or f"Created {entity_type}",
            season_id=season_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    
    async def log_update(
        self,
        entity_type: str,
        entity_id: UUID,
        user_id: Optional[UUID] = None,
        old_data: Optional[dict[str, Any]] = None,
        new_data: Optional[dict[str, Any]] = None,
        description: Optional[str] = None,
        season_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """Log an update action."""
        return await self.log(
            entity_type=entity_type,
            entity_id=entity_id,
            action=AuditAction.UPDATE,
            user_id=user_id,
            old_data=old_data,
            new_data=new_data,
            description=description or f"Updated {entity_type}",
            season_id=season_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    
    async def log_delete(
        self,
        entity_type: str,
        entity_id: UUID,
        user_id: Optional[UUID] = None,
        old_data: Optional[dict[str, Any]] = None,
        description: Optional[str] = None,
        season_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """Log a delete action."""
        return await self.log(
            entity_type=entity_type,
            entity_id=entity_id,
            action=AuditAction.DELETE,
            user_id=user_id,
            old_data=old_data,
            description=description or f"Deleted {entity_type}",
            season_id=season_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    
    async def log_workflow_transition(
        self,
        season_id: UUID,
        user_id: Optional[UUID] = None,
        old_status: Optional[str] = None,
        new_status: Optional[str] = None,
        description: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """Log a workflow status transition."""
        return await self.log(
            entity_type="Season",
            entity_id=season_id,
            action=AuditAction.WORKFLOW_TRANSITION,
            user_id=user_id,
            old_data={"status": old_status} if old_status else None,
            new_data={"status": new_status} if new_status else None,
            description=description or f"Workflow transition: {old_status} -> {new_status}",
            season_id=season_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    
    async def log_upload(
        self,
        entity_type: str,
        entity_id: UUID,
        user_id: Optional[UUID] = None,
        record_count: int = 0,
        description: Optional[str] = None,
        season_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """Log a bulk upload action."""
        return await self.log(
            entity_type=entity_type,
            entity_id=entity_id,
            action=AuditAction.UPLOAD,
            user_id=user_id,
            new_data={"record_count": record_count},
            description=description or f"Uploaded {record_count} {entity_type} records",
            season_id=season_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    
    async def log_lock(
        self,
        season_id: UUID,
        user_id: Optional[UUID] = None,
        description: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """Log a season lock action."""
        return await self.log(
            entity_type="Season",
            entity_id=season_id,
            action=AuditAction.LOCK,
            user_id=user_id,
            description=description or "Season locked for read-only access",
            season_id=season_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
