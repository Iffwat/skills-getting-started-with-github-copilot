import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    original_participants = {
        name: activity["participants"].copy()
        for name, activity in activities.items()
    }

    with TestClient(app, follow_redirects=False) as test_client:
        yield test_client

    for name, participants in original_participants.items():
        activities[name]["participants"][:] = participants


def test_root_redirects_to_static_index(client: TestClient):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/")

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_data_without_cache(client: TestClient):
    # Arrange
    expected_activity = "Art Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert expected_activity in response.json()
    assert response.headers["cache-control"] == "no-store"


def test_signup_adds_participant(client: TestClient):
    # Arrange
    activity = "Art Club"
    email = "new-student@example.edu"

    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity}"}
    assert email in client.get("/activities").json()[activity]["participants"]


def test_signup_rejects_unknown_activity(client: TestClient):
    # Arrange
    activity = "Unknown Club"
    email = "student@example.edu"

    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_duplicate_participant(client: TestClient):
    # Arrange
    activity = "Chess Club"
    email = activities[activity]["participants"][0]

    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"


def test_unregister_removes_participant(client: TestClient):
    # Arrange
    activity = "Art Club"
    email = "registered-student@example.edu"
    activities[activity]["participants"].append(email)

    # Act
    response = client.delete(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity}"}
    assert email not in client.get("/activities").json()[activity]["participants"]


def test_unregister_rejects_unknown_activity(client: TestClient):
    # Arrange
    activity = "Unknown Club"
    email = "student@example.edu"

    # Act
    response = client.delete(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_rejects_unregistered_participant(client: TestClient):
    # Arrange
    activity = "Art Club"
    email = "not-registered@example.edu"

    # Act
    response = client.delete(f"/activities/{activity}/signup", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
