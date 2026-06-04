"""Admin/reviewer user model."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from backend.database import Base


class User(Base):
    """Represents an admin or reviewer user."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(200), nullable=True)
    role = Column(String(20), default="reviewer")  # admin, reviewer
    full_name = Column(String(200), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "full_name": self.full_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
