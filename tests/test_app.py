from copy import deepcopy
import pytest
from fastapi.testclient import TestClient

from src.app import app, activities as activities_db


@pytest.fixture(autouse=True)
def reset_activities():
    """Ensure each test gets a fresh copy of the activities data."""
    global activities_db
    activities_db.clear()
    activities_db.update(deepcopy({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"],
        },
        # include one or two additional activities for coverage
        "Science Club": {
            "description": "Conduct experiments and explore topics in physics, chemistry, and biology",
            "schedule": "Tuesdays, 3:30 PM - 5:00 PM",
            "max_participants": 20,
            "participants": [],
        },
    }))


@pytest.fixture

def client():
    return TestClient(app)


def test_root_redirects_to_static(client):
    # Arrange - nothing special
    # Act
    response = client.get("/", follow_redirects=False)
    # Assert
    assert response.status_code in (307, 302)
    assert "/static/index.html" in response.headers["location"]


def test_get_activities(client):
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert data["Chess Club"]["description"].startswith("Learn strategies")


def test_signup_success(client):
    response = client.post(
        "/activities/Science%20Club/signup?email=alice%40mergington.edu"
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Signed up alice@mergington.edu for Science Club"
    assert "alice@mergington.edu" in activities_db["Science Club"]["participants"]


def test_signup_nonexistent_activity(client):
    response = client.post("/activities/Nonexistent/signup?email=bob%40mergington.edu")
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_duplicate(client):
    response = client.post(
        "/activities/Chess%20Club/signup?email=michael%40mergington.edu"
    )
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"]


def test_unregister_success(client):
    # first sign someone up so we can remove them
    client.post("/activities/Science%20Club/signup?email=carl%40mergington.edu")
    response = client.delete(
        "/activities/Science%20Club/unregister?email=carl%40mergington.edu"
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Unregistered carl@mergington.edu from Science Club"
    assert "carl@mergington.edu" not in activities_db["Science Club"]["participants"]


def test_unregister_nonexistent_activity(client):
    response = client.delete("/activities/Nope/unregister?email=foo%40bar.com")
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_not_signed_up(client):
    response = client.delete(
        "/activities/Science%20Club/unregister?email=ghost%40mergington.edu"
    )
    assert response.status_code == 400
    assert "not signed up" in response.json()["detail"]
