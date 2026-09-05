import os

# Set test secrets before app settings are loaded.
os.environ["SECRET_KEY"] = "test-secret-key-not-for-production"
os.environ["SEED_DEMO_DATA"] = "False"
# Keep tests isolated from external AI/ASR/TTS providers.
os.environ["AI_PROVIDER"] = "mock"
os.environ["VOICE_PROVIDER"] = "mock"

import pytest
from datetime import date, timedelta
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


# --- Shared cycle-tracking helpers ----------------------------------------

FEMALE_PROFILE = {
    "user_name": "Ayesha Test",
    "age": 28,
    "sex": "female",
    "height_cm": 160.0,
    "weight_kg": 55.0,
    "blood_group": "O+",
    "city": "Lahore",
    "language": "en",
}

MALE_PROFILE = {
    "user_name": "Bilal Test",
    "age": 34,
    "sex": "male",
    "height_cm": 172.0,
    "weight_kg": 75.0,
    "blood_group": "O+",
    "city": "Lahore",
    "language": "en",
}


def days_ago(n: int) -> str:
    return (date.today() - timedelta(days=n)).isoformat()


def register_and_login(client, email: str, name: str) -> dict:
    client.post(
        "/api/v1/auth/register",
        json={"name": name, "email": email, "password": "password123"},
    )
    token = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def female_headers(client):
    """A registered female user with a completed profile."""
    headers = register_and_login(client, "female@example.com", "Ayesha Test")
    response = client.post("/api/v1/profile", json=FEMALE_PROFILE, headers=headers)
    assert response.status_code == 201
    return headers


@pytest.fixture
def male_headers(client, auth_headers):
    """A registered male user with a completed profile."""
    response = client.post("/api/v1/profile", json=MALE_PROFILE, headers=auth_headers)
    assert response.status_code == 201
    return auth_headers


@pytest.fixture
def second_female_headers(client):
    headers = register_and_login(client, "female2@example.com", "Sara Test")
    response = client.post(
        "/api/v1/profile", json={**FEMALE_PROFILE, "user_name": "Sara Test"}, headers=headers
    )
    assert response.status_code == 201
    return headers


def create_cycle(client, headers, start: str, period_length: int = 5):
    response = client.post(
        "/api/v1/cycles",
        json={"start_date": start, "period_length": period_length},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()
