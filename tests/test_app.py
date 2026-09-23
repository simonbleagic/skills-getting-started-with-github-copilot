import copy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the in-memory activity data before and after each test."""
    original = copy.deepcopy(activities)

    yield

    activities.clear()
    activities.update(copy.deepcopy(original))


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_root_redirects_to_static_index(client):
    # Arrange
    request_path = "/"

    # Act
    response = client.get(request_path, follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_list(client):
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert expected_activity in payload
    assert "description" in payload[expected_activity]
    assert "schedule" in payload[expected_activity]
    assert "max_participants" in payload[expected_activity]
    assert "participants" in payload[expected_activity]


def test_signup_for_activity_succeeds_and_updates_participants(client):
    # Arrange
    activity_name = "Soccer Club"
    student_email = "new.student@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup?email={student_email}")
    activities_response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {student_email} for {activity_name}"}
    participant_list = activities_response.json()[activity_name]["participants"]
    assert participant_list.count(student_email) == 1


def test_signup_for_duplicate_activity_returns_error(client):
    # Arrange
    activity_name = "Soccer Club"
    student_email = "duplicate.student@mergington.edu"
    client.post(f"/activities/{activity_name}/signup?email={student_email}")

    # Act
    response = client.post(f"/activities/{activity_name}/signup?email={student_email}")
    activities_response = client.get("/activities")

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up for this activity"}
    participant_list = activities_response.json()[activity_name]["participants"]
    assert participant_list.count(student_email) == 1


def test_signup_for_missing_activity_returns_404(client):
    # Arrange
    activity_name = "Ghost Club"
    student_email = "ghost.student@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup?email={student_email}")

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
