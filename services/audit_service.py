"""
Audit Service Module.
Logs user actions, system security events, and data updates to audit_logs table.
"""

import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from database.models import AuditLog

logger = logging.getLogger(__name__)


class AuditService:
    """Service to log and fetch administrative audit trails."""

    @staticmethod
    def log_action(
        db: Session,
        user_id: Optional[int],
        action: str,
        details: str,
        ip_address: str = "127.0.0.1"
    ) -> None:
        """Create audit log entry."""
        try:
            log_entry = AuditLog(
                user_id=user_id,
                action=action.strip(),
                details=details.strip(),
                ip_address=ip_address
            )
            db.add(log_entry)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to record audit log: {e}")

    @staticmethod
    def get_recent_logs(db: Session, limit: int = 100) -> List[AuditLog]:
        """Fetch recent audit log entries ordered by timestamp."""
        return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()
