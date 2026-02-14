"""SQLAlchemy models for database tables"""

from sqlalchemy import Column, String, Integer, Text, DateTime, CheckConstraint, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum

from app.database import Base


class TicketCategory(str, enum.Enum):
    """Ticket category enumeration"""
    BILLING = "billing"
    TECHNICAL = "technical"
    FEATURE_REQUEST = "feature_request"


class TicketUrgency(str, enum.Enum):
    """Ticket urgency enumeration"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TicketStatus(str, enum.Enum):
    """Ticket status enumeration"""
    PENDING = "pending"          # Just created, waiting for worker
    PROCESSING = "processing"    # Worker is processing
    READY = "ready"              # AI processing complete, ready for agent
    RESOLVED = "resolved"        # Agent has resolved
    FAILED = "failed"            # Processing failed


class Ticket(Base):
    """Main tickets table"""
    __tablename__ = "tickets"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # User Input Fields
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    customer_email = Column(String(255), nullable=False)
    customer_name = Column(String(100), nullable=True)
    
    # AI-Generated Fields
    category = Column(SQLEnum(TicketCategory), nullable=True)
    sentiment_score = Column(Integer, nullable=True)
    urgency = Column(SQLEnum(TicketUrgency), nullable=True)
    ai_draft_response = Column(Text, nullable=True)
    
    # Agent Fields
    final_response = Column(Text, nullable=True)
    agent_notes = Column(Text, nullable=True)
    resolved_by = Column(String(100), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Status Tracking Fields
    status = Column(SQLEnum(TicketStatus), nullable=False, default=TicketStatus.PENDING)
    error_message = Column(Text, nullable=True)
    processing_attempts = Column(Integer, nullable=False, default=0)
    
    # Metadata Fields
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            'sentiment_score IS NULL OR (sentiment_score >= 1 AND sentiment_score <= 10)',
            name='valid_sentiment_score'
        ),
        CheckConstraint(
            'processing_attempts >= 0',
            name='valid_processing_attempts'
        ),
        CheckConstraint(
            "TRIM(title) != ''",
            name='non_empty_title'
        ),
        CheckConstraint(
            "TRIM(description) != ''",
            name='non_empty_description'
        ),
    )
    
    def __repr__(self):
        return f"<Ticket(id={self.id}, title='{self.title[:30]}...', status={self.status})>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "title": self.title,
            "description": self.description,
            "customer_email": self.customer_email,
            "customer_name": self.customer_name,
            "category": self.category.value if self.category else None,
            "sentiment_score": self.sentiment_score,
            "urgency": self.urgency.value if self.urgency else None,
            "ai_draft_response": self.ai_draft_response,
            "final_response": self.final_response,
            "agent_notes": self.agent_notes,
            "resolved_by": self.resolved_by,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "status": self.status.value,
            "error_message": self.error_message,
            "processing_attempts": self.processing_attempts,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
