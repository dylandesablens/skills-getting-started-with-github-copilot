"""
Tests for the Mergington High School Activities API

Tests follow the Arrange-Act-Assert (AAA) pattern:
- Arrange: Set up test fixtures and data
- Act: Execute the operation being tested
- Assert: Verify the results match expectations
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """
    Arrange: Create a TestClient for the FastAPI app
    
    This fixture provides a client that can make HTTP requests to the app
    without running a server. Scope is function-level to ensure each test
    gets a fresh client instance.
    """
    return TestClient(app)


@pytest.fixture
def fresh_activities(monkeypatch):
    """
    Arrange: Provide a fresh activities dictionary for each test
    
    This fixture ensures test isolation by resetting the activities dict
    to a known state before each test. Uses monkeypatch to replace the
    module-level activities dict.
    """
    test_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Basketball Team": {
            "description": "Competitive basketball team for students of all skill levels",
            "schedule": "Mondays and Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["james@mergington.edu"]
        },
    }
    monkeypatch.setattr("src.app.activities", test_activities)
    return test_activities


class TestGetActivities:
    """Test suite for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client, fresh_activities):
        """
        Arrange: TestClient and fresh activities fixture
        Act: Make a GET request to /activities
        Assert: Verify response status and all activities are returned
        """
        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Basketball Team" in data

    def test_get_activities_returns_correct_structure(self, client, fresh_activities):
        """
        Arrange: TestClient and fresh activities fixture
        Act: Make a GET request to /activities
        Assert: Verify each activity has required fields
        """
        # Act
        response = client.get("/activities")

        # Assert
        data = response.json()
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club

    def test_get_activities_includes_participants(self, client, fresh_activities):
        """
        Arrange: TestClient and fresh activities fixture
        Act: Make a GET request to /activities
        Assert: Verify participants list is included with correct values
        """
        # Act
        response = client.get("/activities")

        # Assert
        data = response.json()
        chess_participants = data["Chess Club"]["participants"]
        assert len(chess_participants) == 2
        assert "michael@mergington.edu" in chess_participants
        assert "daniel@mergington.edu" in chess_participants


class TestSignupForActivity:
    """Test suite for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_adds_student_to_activity(self, client, fresh_activities):
        """
        Arrange: TestClient, fresh activities, and a new student email
        Act: Make a POST request to signup endpoint
        Assert: Verify student is added to the activity's participants list
        """
        # Arrange
        new_student = "alex@mergington.edu"

        # Act
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": new_student}
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {new_student} for Chess Club"
        assert new_student in fresh_activities["Chess Club"]["participants"]

    def test_signup_returns_success_message(self, client, fresh_activities):
        """
        Arrange: TestClient and fresh activities
        Act: Make a POST request to signup
        Assert: Verify response contains correct success message
        """
        # Arrange
        new_student = "alex@mergington.edu"

        # Act
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": new_student}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert new_student in data["message"]
        assert "Chess Club" in data["message"]

    def test_signup_fails_for_nonexistent_activity(self, client, fresh_activities):
        """
        Arrange: TestClient, fresh activities, and a nonexistent activity name
        Act: Make a POST request to signup for a non-existent activity
        Assert: Verify request fails with 404 status and descriptive error
        """
        # Arrange
        new_student = "alex@mergington.edu"

        # Act
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": new_student}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"

    def test_signup_fails_for_duplicate_signup(self, client, fresh_activities):
        """
        Arrange: TestClient, fresh activities, existing participant
        Act: Make a POST request to signup with already-registered email
        Assert: Verify request fails with 400 status
        """
        # Arrange
        existing_student = "michael@mergington.edu"

        # Act
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": existing_student}
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert data["detail"] == "Student already signed up for this activity"

    def test_signup_increments_participant_count(self, client, fresh_activities):
        """
        Arrange: TestClient, fresh activities, new student email
        Act: Make a POST request to signup and capture initial count
        Assert: Verify participant count increased by one
        """
        # Arrange
        new_student = "alex@mergington.edu"
        initial_count = len(fresh_activities["Chess Club"]["participants"])

        # Act
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": new_student}
        )

        # Assert
        assert response.status_code == 200
        final_count = len(fresh_activities["Chess Club"]["participants"])
        assert final_count == initial_count + 1


class TestUnregisterFromActivity:
    """Test suite for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_removes_student_from_activity(self, client, fresh_activities):
        """
        Arrange: TestClient, fresh activities, existing participant
        Act: Make a DELETE request to unregister
        Assert: Verify student is removed from participants list
        """
        # Arrange
        student_to_remove = "michael@mergington.edu"

        # Act
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": student_to_remove}
        )

        # Assert
        assert response.status_code == 200
        assert student_to_remove not in fresh_activities["Chess Club"]["participants"]

    def test_unregister_returns_success_message(self, client, fresh_activities):
        """
        Arrange: TestClient and existing participant
        Act: Make a DELETE request to unregister
        Assert: Verify response contains success message
        """
        # Arrange
        student_to_remove = "michael@mergington.edu"

        # Act
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": student_to_remove}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert student_to_remove in data["message"]
        assert "Chess Club" in data["message"]

    def test_unregister_fails_for_nonexistent_activity(self, client, fresh_activities):
        """
        Arrange: TestClient and nonexistent activity name
        Act: Make a DELETE request for nonexistent activity
        Assert: Verify request fails with 404 status
        """
        # Arrange
        student = "michael@mergington.edu"

        # Act
        response = client.delete(
            "/activities/Nonexistent Club/unregister",
            params={"email": student}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"

    def test_unregister_fails_for_student_not_in_activity(self, client, fresh_activities):
        """
        Arrange: TestClient and student not registered for activity
        Act: Make a DELETE request for unregistered student
        Assert: Verify request fails with 404 status
        """
        # Arrange
        student_not_registered = "nonexistent@mergington.edu"

        # Act
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": student_not_registered}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Student not found in this activity"

    def test_unregister_decrements_participant_count(self, client, fresh_activities):
        """
        Arrange: TestClient, existing participant, initial count
        Act: Make a DELETE request to unregister
        Assert: Verify participant count decreased by one
        """
        # Arrange
        student_to_remove = "michael@mergington.edu"
        initial_count = len(fresh_activities["Chess Club"]["participants"])

        # Act
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": student_to_remove}
        )

        # Assert
        assert response.status_code == 200
        final_count = len(fresh_activities["Chess Club"]["participants"])
        assert final_count == initial_count - 1

    def test_unregister_preserves_other_participants(self, client, fresh_activities):
        """
        Arrange: TestClient and activity with multiple participants
        Act: Make a DELETE request for one student
        Assert: Verify other participants remain unchanged
        """
        # Arrange
        student_to_remove = "michael@mergington.edu"
        other_student = "daniel@mergington.edu"

        # Act
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": student_to_remove}
        )

        # Assert
        assert response.status_code == 200
        assert other_student in fresh_activities["Chess Club"]["participants"]
