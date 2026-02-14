"""WebSocket endpoint for real-time ticket updates"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List, Dict
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept and store a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New WebSocket connection. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific connection"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
    
    async def broadcast(self, message: str):
        """Broadcast a message to all connected clients"""
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
        
        if self.active_connections:
            logger.info(f"Broadcasted message to {len(self.active_connections)} clients")


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws/tickets")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time ticket updates.
    
    Clients can connect to receive real-time notifications about ticket status changes.
    
    Message format:
    {
        "type": "ticket_update",
        "ticket_id": "uuid",
        "status": "ready|processing|resolved|failed",
        "data": {...}
    }
    """
    await manager.connect(websocket)
    
    try:
        # Send welcome message
        await websocket.send_json({
            "type": "connection_established",
            "message": "Connected to Complaint Triage System WebSocket"
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client (e.g., ping/pong)
                data = await websocket.receive_text()
                
                # Handle ping-pong
                if data == "ping":
                    await websocket.send_text("pong")
                else:
                    # Echo back for testing
                    await websocket.send_json({
                        "type": "echo",
                        "message": data
                    })
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"Error in WebSocket loop: {e}")
                break
    
    except WebSocketDisconnect:
        logger.info("Client disconnected normally")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)


async def broadcast_ticket_update(ticket_id: str, status: str, data: Dict = None):
    """
    Helper function to broadcast ticket updates to all connected clients.
    
    Call this function from Celery worker or API endpoints when ticket status changes.
    
    Args:
        ticket_id: UUID of the ticket
        status: New status of the ticket
        data: Optional additional data about the ticket
    """
    message = {
        "type": "ticket_update",
        "ticket_id": ticket_id,
        "status": status,
        "timestamp": asyncio.get_event_loop().time(),
        "data": data or {}
    }
    
    await manager.broadcast(json.dumps(message))


async def broadcast_ticket_created(ticket_id: str, title: str):
    """Broadcast notification when a new ticket is created"""
    message = {
        "type": "ticket_created",
        "ticket_id": ticket_id,
        "title": title,
        "timestamp": asyncio.get_event_loop().time()
    }
    
    await manager.broadcast(json.dumps(message))


async def broadcast_ticket_resolved(ticket_id: str, resolved_by: str):
    """Broadcast notification when a ticket is resolved"""
    message = {
        "type": "ticket_resolved",
        "ticket_id": ticket_id,
        "resolved_by": resolved_by,
        "timestamp": asyncio.get_event_loop().time()
    }
    
    await manager.broadcast(json.dumps(message))
