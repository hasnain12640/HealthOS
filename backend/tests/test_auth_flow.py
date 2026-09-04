import pytest


PROFILE_PAYLOAD = {
    "user_name": "Test User",
    "age": 34,
    "sex": "male",
    "height_cm": 172.0,
    "weight_kg": 75.0,
    "blood_group": "O+",
    "city": "Lahore",
    "language": "en",
}


@pytest.fixture
def second_user_headers(client):
    """Register a second user and return their auth headers."""
    client.post(
        "/api/v1/auth/register",
        json={"name": "Other User", "email": "other@example.com", "password": "password123"},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "other@example.com", "password": "password123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_register_creates_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={"name": "New User", "email": "new@example.com", "password": "password123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user"]["email"] == "new@example.com"
    assert data["user"]["name"] == "New User"
    assert "access_token" in data


def test_register_duplicate_email_rejected(client):
    payload = {"name": "New User", "email": "duplicate@example.com", "password": "password123"}
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201

    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "already" in response.json()["detail"].lower()


def test_login_success_and_wrong_password(client):
    client.post(
        "/api/v1/auth/register",
        json={"name": "Login User", "email": "login@example.com", "password": "password123"},
    )

    success = client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "password123"},
    )
    assert success.status_code == 200
    assert "access_token" in success.json()

    failure = client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "wrongpassword"},
    )
    assert failure.status_code == 401


def test_me_returns_current_user(client, auth_headers):
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"


def test_logout(client, auth_headers):
    response = client.post("/api/v1/auth/logout", headers=auth_headers)
    assert response.status_code == 200


def test_unauthorized_access_blocked(client):
    protected = [
        ("get", "/api/v1/dashboard"),
        ("get", "/api/v1/analysis"),
        ("post", "/api/v1/chat"),
        ("post", "/api/v1/plan"),
        ("post", "/api/v1/insights"),
        ("get", "/api/v1/profile/me"),
        ("post", "/api/v1/profile"),
        ("get", "/api/v1/lab"),
        ("post", "/api/v1/lifestyle/nutrition"),
    ]
    for method, path in protected:
        response = client.request(method, path)
        assert response.status_code == 401, f"{method.upper()} {path} should require auth"


def test_onboarding_persistence(client, auth_headers):
    response = client.post("/api/v1/profile", json=PROFILE_PAYLOAD, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["user_name"] == PROFILE_PAYLOAD["user_name"]
    assert data["age"] == PROFILE_PAYLOAD["age"]

    me = client.get("/api/v1/profile/me", headers=auth_headers)
    assert me.status_code == 200
    assert me.json()["city"] == PROFILE_PAYLOAD["city"]


def test_onboarding_rejected_when_profile_exists(client, auth_headers):
    client.post("/api/v1/profile", json=PROFILE_PAYLOAD, headers=auth_headers)
    response = client.post("/api/v1/profile", json=PROFILE_PAYLOAD, headers=auth_headers)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()


def test_dashboard_after_onboarding(client, auth_headers):
    client.post("/api/v1/profile", json=PROFILE_PAYLOAD, headers=auth_headers)

    response = client.get("/api/v1/dashboard", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["profile"]["user_name"] == PROFILE_PAYLOAD["user_name"]
    assert "hydration" in data
    assert "nutrition" in data
    assert "priorities" in data


def test_cross_user_isolation(client, auth_headers, second_user_headers):
    # User A creates a profile and a manual lab report.
    profile_response = client.post("/api/v1/profile", json=PROFILE_PAYLOAD, headers=auth_headers)
    profile_id = profile_response.json()["id"]

    report = client.post(
        "/api/v1/lab/manual",
        json={
            "lab_name": "Test Lab",
            "report_date": "2024-08-15",
            "biomarkers": [
                {"name": "Hemoglobin", "value": 13.5, "unit": "g/dL", "reference_low": 13.0, "reference_high": 17.0}
            ],
        },
        headers=auth_headers,
    )
    assert report.status_code == 201
    report_id = report.json()["id"]

    # User B cannot see User A's report detail.
    detail = client.get(f"/api/v1/lab/detail/{report_id}", headers=second_user_headers)
    assert detail.status_code == 404

    # User B's dashboard is empty / separate.
    client.post("/api/v1/profile", json={**PROFILE_PAYLOAD, "user_name": "Other User"}, headers=second_user_headers)
    dashboard = client.get("/api/v1/dashboard", headers=second_user_headers)
    assert dashboard.status_code == 200
    assert dashboard.json()["profile"]["user_name"] == "Other User"
    assert dashboard.json()["lab_summary"]["report_id"] is None


def test_demo_account_login(client):
    # Simulate the demo account normally created from environment variables.
    client.post(
        "/api/v1/auth/register",
        json={"name": "Bilal Ahmed", "email": "demo@healthos.pk", "password": "demopass123"},
    )
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "demo@healthos.pk", "password": "demopass123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == "demo@healthos.pk"
    assert "access_token" in data
