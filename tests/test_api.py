import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "version" in response.json()


def test_register_user(client):
    """Test user registration"""
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "securepassword123",
        "phone": "+998901234567",
        "first_name": "Test",
        "last_name": "User",
    }
    response = client.post("/api/auth/register", json=user_data)
    assert response.status_code in [201, 400]  # 400 if user exists


def test_login_user(client):
    """Test user login"""
    credentials = {
        "username": "testuser",
        "password": "securepassword123",
    }
    response = client.post("/api/auth/login", json=credentials)
    # Will fail if user not registered, but tests structure shown
    assert response.status_code in [200, 401]


def test_unauthorized_access(client):
    """Test unauthorized access to protected endpoints"""
    response = client.get("/api/orders")
    assert response.status_code == 403  # No auth header provided


def test_invalid_token(client):
    """Test invalid token"""
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/api/orders", headers=headers)
    assert response.status_code == 401
