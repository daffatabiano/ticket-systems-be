"""REST API endpoints for ticket management"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime
import logging

from app.database import get_db
from app.models import Ticket, TicketStatus, TicketUrgency, TicketCategory
from app.schemas import (
    TicketCreate, TicketCreateResponse, TicketResponse, 
    TicketListResponse, TicketUpdate, TicketResolve
)
from app.workers.celery_worker import process_ticket_task

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


@router.post("/", response_model=TicketCreateResponse, status_code=201)
async def create_ticket(
    ticket_data: TicketCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new ticket and queue it for AI processing.
    
    **CRITICAL: This endpoint returns immediately (< 200ms) without waiting for AI processing.**
    
    The ticket is created with status='pending' and a background worker picks it up
    for AI analysis (which takes 3-5 seconds).
    """
    try:
        # Create ticket in database with PENDING status
        ticket = Ticket(
            title=ticket_data.title,
            description=ticket_data.description,
            customer_email=ticket_data.customer_email,
            customer_name=ticket_data.customer_name,
            status=TicketStatus.PENDING,
            processing_attempts=0
        )
        
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        
        logger.info(f"✅ Created ticket {ticket.id} with status PENDING")
        
        # Queue background task for AI processing (NON-BLOCKING)
        process_ticket_task.delay(str(ticket.id))
        
        logger.info(f"📤 Queued ticket {ticket.id} for background processing")
        
        # Return immediately without waiting for AI processing
        return TicketCreateResponse(
            id=ticket.id,
            status=ticket.status,
            message="Ticket created successfully and queued for processing"
        )
        
    except Exception as e:
        logger.error(f"Error creating ticket: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating ticket: {str(e)}")


@router.get("/", response_model=TicketListResponse)
async def list_tickets(
    status: Optional[TicketStatus] = Query(None, description="Filter by status"),
    urgency: Optional[TicketUrgency] = Query(None, description="Filter by urgency"),
    category: Optional[TicketCategory] = Query(None, description="Filter by category"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db)
):
    """
    Get a list of tickets with optional filters.
    
    - **status**: Filter by ticket status (pending, processing, ready, resolved, failed)
    - **urgency**: Filter by urgency level (high, medium, low)
    - **category**: Filter by category (billing, technical, feature_request)
    - **limit**: Maximum number of results to return (default: 100)
    - **offset**: Number of results to skip for pagination (default: 0)
    """
    try:
        # Build query
        query = db.query(Ticket)
        
        # Apply filters
        if status:
            query = query.filter(Ticket.status == status)
        if urgency:
            query = query.filter(Ticket.urgency == urgency)
        if category:
            query = query.filter(Ticket.category == category)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        tickets = query.order_by(
            Ticket.created_at.desc()
        ).limit(limit).offset(offset).all()
        
        return TicketListResponse(total=total, items=tickets)
        
    except Exception as e:
        logger.error(f"Error listing tickets: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing tickets: {str(e)}")


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific ticket by ID.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    
    return ticket


@router.patch("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: UUID,
    ticket_update: TicketUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a ticket (agent editing the draft response or adding notes).
    
    This allows agents to edit the AI-generated draft before resolving.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    
    try:
        # Update fields if provided
        if ticket_update.final_response is not None:
            ticket.final_response = ticket_update.final_response
        if ticket_update.agent_notes is not None:
            ticket.agent_notes = ticket_update.agent_notes
        
        ticket.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(ticket)
        
        logger.info(f"✅ Updated ticket {ticket_id}")
        
        return ticket
        
    except Exception as e:
        logger.error(f"Error updating ticket {ticket_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating ticket: {str(e)}")


@router.post("/{ticket_id}/resolve", response_model=TicketResponse)
async def resolve_ticket(
    ticket_id: UUID,
    resolve_data: TicketResolve,
    db: Session = Depends(get_db)
):
    """
    Resolve a ticket.
    
    Marks the ticket as resolved with the final response and agent information.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    
    if ticket.status == TicketStatus.RESOLVED:
        raise HTTPException(status_code=400, detail="Ticket is already resolved")
    
    try:
        # Update ticket with resolution data
        ticket.final_response = resolve_data.final_response
        ticket.agent_notes = resolve_data.agent_notes
        ticket.resolved_by = resolve_data.resolved_by
        ticket.resolved_at = datetime.utcnow()
        ticket.status = TicketStatus.RESOLVED
        ticket.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(ticket)
        
        logger.info(f"✅ Resolved ticket {ticket_id} by {resolve_data.resolved_by}")
        
        return ticket
        
    except Exception as e:
        logger.error(f"Error resolving ticket {ticket_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error resolving ticket: {str(e)}")


@router.delete("/{ticket_id}", status_code=204)
async def delete_ticket(
    ticket_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a ticket.
    
    **Warning:** This permanently deletes the ticket. Use with caution.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
    
    try:
        db.delete(ticket)
        db.commit()
        
        logger.info(f"🗑️  Deleted ticket {ticket_id}")
        
        return None
        
    except Exception as e:
        logger.error(f"Error deleting ticket {ticket_id}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting ticket: {str(e)}")


@router.get("/stats/summary")
async def get_ticket_stats(db: Session = Depends(get_db)):
    """
    Get ticket statistics summary.
    """
    try:
        total = db.query(Ticket).count()
        pending = db.query(Ticket).filter(Ticket.status == TicketStatus.PENDING).count()
        processing = db.query(Ticket).filter(Ticket.status == TicketStatus.PROCESSING).count()
        ready = db.query(Ticket).filter(Ticket.status == TicketStatus.READY).count()
        resolved = db.query(Ticket).filter(Ticket.status == TicketStatus.RESOLVED).count()
        failed = db.query(Ticket).filter(Ticket.status == TicketStatus.FAILED).count()
        
        high_urgency = db.query(Ticket).filter(Ticket.urgency == TicketUrgency.HIGH).count()
        medium_urgency = db.query(Ticket).filter(Ticket.urgency == TicketUrgency.MEDIUM).count()
        low_urgency = db.query(Ticket).filter(Ticket.urgency == TicketUrgency.LOW).count()
        
        return {
            "total": total,
            "by_status": {
                "pending": pending,
                "processing": processing,
                "ready": ready,
                "resolved": resolved,
                "failed": failed
            },
            "by_urgency": {
                "high": high_urgency,
                "medium": medium_urgency,
                "low": low_urgency
            }
        }
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting statistics: {str(e)}")
