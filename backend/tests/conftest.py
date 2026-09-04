import os

# Set test secrets before app settings are loaded.
os.environ["SECRET_KEY"] = "test-secret-key-not-for-production"
os.environ["SEED_DEMO_DATA"] = "False"

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import app

TEST_DB_URL = "sqlite:///./test_healthos.db"

engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function", autouse=True)
def setup_test_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(client):
    """Register a test user, log in, and return auth headers."""
    register_payload = {
        "name": "Test User",
        "email": "test@example.com",
        "password": "password123",
    }
    client.post("/api/v1/auth/register", json=register_payload)

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
