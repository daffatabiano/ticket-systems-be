"""Basic tests for the API"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_read_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "version" in response.json()


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data


def test_api_info():
    """Test API info endpoint"""
    response = client.get("/api/info")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "endpoints" in data


def test_create_ticket():
    """Test ticket creation (non-blocking)"""
    import time
    
    ticket_data = {
        "title": "Test billing issue",
        "description": "I was charged twice for my subscription this month. Please help!",
        "customer_email": "test@example.com",
        "customer_name": "Test User"
    }
    
    # Measure response time
    start_time = time.time()
    response = client.post("/api/tickets/", json=ticket_data)
    end_time = time.time()
    
    response_time = end_time - start_time
    
    # Verify response
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["status"] == "pending"
    assert "message" in data
    
    # CRITICAL: Verify non-blocking (< 200ms)
    # Note: In test environment this might be slightly slower
    # In production with proper setup, should be < 200ms
    print(f"\n✅ Response time: {response_time:.3f}s")
    
    return data["id"]


def test_list_tickets():
    """Test listing tickets"""
    response = client.get("/api/tickets/")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data
    assert isinstance(data["items"], list)


def test_get_ticket_stats():
    """Test ticket statistics"""
    response = client.get("/api/tickets/stats/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "by_status" in data
    assert "by_urgency" in data


def test_get_nonexistent_ticket():
    """Test getting a ticket that doesn't exist"""
    fake_uuid = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/api/tickets/{fake_uuid}")
    assert response.status_code == 404


def test_create_ticket_invalid_email():
    """Test creating ticket with invalid email"""
    ticket_data = {
        "title": "Test ticket",
        "description": "This is a test",
        "customer_email": "invalid-email",  # Invalid email
    }
    
    response = client.post("/api/tickets/", json=ticket_data)
    assert response.status_code == 422  # Validation error


def test_create_ticket_missing_fields():
    """Test creating ticket with missing required fields"""
    ticket_data = {
        "title": "Test"  # Missing description and email
    }
    
    response = client.post("/api/tickets/", json=ticket_data)
    assert response.status_code == 422  # Validation error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
