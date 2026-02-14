"""Pydantic schemas for request/response validation"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.models import TicketCategory, TicketUrgency, TicketStatus


# Request Schemas
class TicketCreate(BaseModel):
    """Schema for creating a new ticket"""
    title: str = Field(..., min_length=5, max_length=255, description="Ticket title")
    description: str = Field(..., min_length=10, description="Detailed description of the complaint")
    customer_email: EmailStr = Field(..., description="Customer email address")
    customer_name: Optional[str] = Field(None, max_length=100, description="Customer name")


class TicketUpdate(BaseModel):
    """Schema for updating a ticket (agent editing draft)"""
    final_response: Optional[str] = Field(None, description="Final response to customer")
    agent_notes: Optional[str] = Field(None, description="Internal notes from agent")


class TicketResolve(BaseModel):
    """Schema for resolving a ticket"""
    final_response: str = Field(..., min_length=10, description="Final response to customer")
    agent_notes: Optional[str] = Field(None, description="Internal notes from agent")
    resolved_by: str = Field(..., min_length=2, max_length=100, description="Name of agent resolving the ticket")


# Response Schemas
class TicketResponse(BaseModel):
    """Schema for ticket response"""
    id: UUID
    title: str
    description: str
    customer_email: str
    customer_name: Optional[str]
    
    category: Optional[TicketCategory]
    sentiment_score: Optional[int]
    urgency: Optional[TicketUrgency]
    ai_draft_response: Optional[str]
    
    final_response: Optional[str]
    agent_notes: Optional[str]
    resolved_by: Optional[str]
    resolved_at: Optional[datetime]
    
    status: TicketStatus
    error_message: Optional[str]
    processing_attempts: int
    
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class TicketListResponse(BaseModel):
    """Schema for list of tickets"""
    total: int
    items: list[TicketResponse]


class TicketCreateResponse(BaseModel):
    """Schema for ticket creation response"""
    id: UUID
    status: TicketStatus
    message: str = "Ticket created successfully and queued for processing"


class HealthResponse(BaseModel):
    """Schema for health check response"""
    status: str
    timestamp: datetime
    version: str = "1.0.0"
