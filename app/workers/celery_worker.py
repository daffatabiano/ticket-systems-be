"""Celery worker for background task processing"""

from celery import Celery
from app.config import get_settings
from app.database import SessionLocal
from app.models import Ticket, TicketStatus, TicketCategory, TicketUrgency
from app.services.ai_service import ai_service
import logging
from sqlalchemy.orm import Session
from datetime import datetime

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize Celery
celery_app = Celery(
    "complaint_triage",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30,  # Hard time limit: 30 seconds
    task_soft_time_limit=25,  # Soft time limit: 25 seconds
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def process_ticket_task(self, ticket_id: str):
    """
    Background task to process a ticket with AI analysis.
    
    Args:
        ticket_id: UUID of the ticket to process
        
    Returns:
        dict: Processing result with status and data
    """
    db = SessionLocal()
    
    try:
        logger.info(f"Starting to process ticket: {ticket_id}")
        
        # Get ticket from database
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        
        if not ticket:
            logger.error(f"Ticket not found: {ticket_id}")
            return {"status": "error", "message": "Ticket not found"}
        
        # Update status to PROCESSING
        ticket.status = TicketStatus.PROCESSING
        ticket.processing_attempts += 1
        ticket.updated_at = datetime.utcnow()
        db.commit()
        logger.info(f"Ticket {ticket_id} status updated to PROCESSING (attempt {ticket.processing_attempts})")
        
        try:
            # Call AI service to analyze the ticket
            logger.info(f"Calling AI service for ticket {ticket_id}")
            ai_result = ai_service.analyze_ticket(
                title=ticket.title,
                description=ticket.description,
                customer_name=ticket.customer_name
            )
            
            logger.info(f"AI analysis complete for ticket {ticket_id}: {ai_result}")
            
            # Update ticket with AI results
            ticket.category = TicketCategory(ai_result["category"])
            ticket.sentiment_score = ai_result["sentiment_score"]
            ticket.urgency = TicketUrgency(ai_result["urgency"])
            ticket.ai_draft_response = ai_result["draft_response"]
            ticket.status = TicketStatus.READY
            ticket.error_message = None
            ticket.updated_at = datetime.utcnow()
            
            db.commit()
            
            logger.info(f"✅ Successfully processed ticket {ticket_id}")
            
            return {
                "status": "success",
                "ticket_id": ticket_id,
                "category": ai_result["category"],
                "urgency": ai_result["urgency"],
                "sentiment_score": ai_result["sentiment_score"]
            }
            
        except Exception as ai_error:
            logger.error(f"AI processing error for ticket {ticket_id}: {ai_error}")
            
            # Check if we should retry
            if ticket.processing_attempts < 3:
                # Update status back to PENDING for retry
                ticket.status = TicketStatus.PENDING
                ticket.error_message = f"Retry {ticket.processing_attempts}/3: {str(ai_error)}"
                db.commit()
                
                # Retry the task
                logger.info(f"Retrying ticket {ticket_id} (attempt {ticket.processing_attempts + 1}/3)")
                raise self.retry(exc=ai_error, countdown=10)
            else:
                # Max retries reached, mark as FAILED
                ticket.status = TicketStatus.FAILED
                ticket.error_message = f"Failed after {ticket.processing_attempts} attempts: {str(ai_error)}"
                ticket.updated_at = datetime.utcnow()
                db.commit()
                
                logger.error(f"❌ Failed to process ticket {ticket_id} after {ticket.processing_attempts} attempts")
                
                return {
                    "status": "failed",
                    "ticket_id": ticket_id,
                    "error": str(ai_error)
                }
    
    except Exception as e:
        logger.error(f"Unexpected error processing ticket {ticket_id}: {e}")
        
        # Try to update ticket status to FAILED
        try:
            ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
            if ticket:
                ticket.status = TicketStatus.FAILED
                ticket.error_message = f"Unexpected error: {str(e)}"
                ticket.updated_at = datetime.utcnow()
                db.commit()
        except:
            pass
        
        return {
            "status": "error",
            "ticket_id": ticket_id,
            "error": str(e)
        }
    
    finally:
        db.close()


@celery_app.task
def health_check():
    """Health check task for monitoring"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# For running the worker:
# celery -A app.workers.celery_worker worker --loglevel=info
