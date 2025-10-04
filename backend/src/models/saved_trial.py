"""
Saved trial model for storing user's saved clinical trials.
"""
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid

from .base import Base


class SavedTrial(Base):
    """Model for storing saved clinical trials."""
    
    __tablename__ = "saved_trials"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, default="demo_user")  # For demo purposes
    trial_id = Column(String, nullable=False)  # NCT ID
    trial_data = Column(JSON, nullable=False)  # Full trial match data
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "trial_id": self.trial_id,
            "trial_data": self.trial_data,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }