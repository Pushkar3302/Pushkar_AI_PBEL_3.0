"""
Notification Service Module.
Dispatches and fetches system alerts and early warning notifications.
"""

from typing import List, Tuple
from sqlalchemy.orm import Session
from database.models import Notification


class NotificationService:
    """Service handling in-app notifications and risk warnings."""

    @staticmethod
    def send_notification(
        db: Session,
        user_id: int,
        title: str,
        message: str,
        notification_type: str = "INFO"
    ) -> Tuple[bool, str]:
        """Dispatch notification to a specific user."""
        try:
            notif = Notification(
                user_id=user_id,
                title=title.strip(),
                message=message.strip(),
                notification_type=notification_type.upper()
            )
            db.add(notif)
            db.commit()
            return True, "Notification sent."
        except Exception as e:
            db.rollback()
            return False, f"Failed to send notification: {str(e)}"

    @staticmethod
    def get_user_notifications(db: Session, user_id: int) -> List[Notification]:
        """Fetch unread and read notifications for user."""
        return db.query(Notification).filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()

    @staticmethod
    def mark_as_read(db: Session, notification_id: int) -> bool:
        """Mark notification as read."""
        try:
            n = db.query(Notification).filter_by(id=notification_id).first()
            if n:
                n.is_read = True
                db.commit()
                return True
            return False
        except Exception:
            db.rollback()
            return False
