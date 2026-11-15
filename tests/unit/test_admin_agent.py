"""Unit tests for Admin Agent functionality."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from src.admin_agent.admin_agent import AdminAgent
from src.config.settings import Settings


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    settings = Mock(spec=Settings)
    settings.openai_api_key = "test-key"
    settings.groq_api_key = None
    settings.llm_model = "gpt-3.5-turbo"
    settings.admin_api_url = "http://127.0.0.1:5000"
    settings.admin_api_port = 5000
    return settings


@pytest.fixture
def admin_agent(mock_settings):
    """Create admin agent for testing."""
    with patch('src.admin_agent.admin_agent.ChatOpenAI'):
        agent = AdminAgent(mock_settings)
        return agent


class TestAdminAgent:
    """Tests for AdminAgent class."""

    def test_initialization(self, admin_agent):
        """Test admin agent initialization."""
        assert admin_agent is not None
        assert hasattr(admin_agent, 'pending_requests')
        assert isinstance(admin_agent.pending_requests, dict)
        assert len(admin_agent.pending_requests) == 0

    def test_add_pending_request(self, admin_agent):
        """Test adding a pending reservation request."""
        reservation_data = {
            "first_name": "John",
            "last_name": "Doe",
            "car_number": "ABC123",
            "start_time": "2024-12-25 14:00",
            "end_time": "2024-12-25 18:00"
        }

        result = admin_agent.add_pending_request(1, reservation_data)

        assert result is True
        assert 1 in admin_agent.pending_requests
        assert admin_agent.pending_requests[1]["first_name"] == "John"
        assert admin_agent.pending_requests[1]["status"] == "pending"
        assert "requested_at" in admin_agent.pending_requests[1]

    def test_get_pending_requests_empty(self, admin_agent):
        """Test getting pending requests when none exist."""
        result = admin_agent.get_pending_requests()

        assert "No pending reservation requests" in result

    def test_get_pending_requests_with_data(self, admin_agent):
        """Test getting pending requests with existing data."""
        # Add test data
        admin_agent.add_pending_request(1, {
            "first_name": "John",
            "last_name": "Doe",
            "car_number": "ABC123",
            "start_time": "2024-12-25 14:00",
            "end_time": "2024-12-25 18:00"
        })

        result = admin_agent.get_pending_requests()

        assert "Reservation ID: 1" in result
        assert "John Doe" in result
        assert "ABC123" in result

    def test_get_request_details_not_found(self, admin_agent):
        """Test getting details for non-existent reservation."""
        result = admin_agent.get_request_details(999)

        assert "No request found" in result
        assert "999" in result

    def test_get_request_details_found(self, admin_agent):
        """Test getting details for existing reservation."""
        admin_agent.add_pending_request(1, {
            "first_name": "John",
            "last_name": "Doe",
            "car_number": "ABC123",
            "start_time": "2024-12-25 14:00",
            "end_time": "2024-12-25 18:00"
        })

        result = admin_agent.get_request_details(1)

        assert "Reservation ID: 1" in result
        assert "John" in result
        assert "Doe" in result
        assert "ABC123" in result

    def test_process_admin_decision_approve(self, admin_agent):
        """Test approving a reservation."""
        # Add a pending request
        admin_agent.add_pending_request(1, {
            "first_name": "John",
            "last_name": "Doe",
            "car_number": "ABC123",
            "start_time": "2024-12-25 14:00",
            "end_time": "2024-12-25 18:00"
        })

        # Approve it
        result = admin_agent.process_admin_decision(
            reservation_id=1,
            decision="approved",
            admin_notes="Looks good"
        )

        assert result["success"] is True
        assert result["decision"] == "approved"
        assert result["admin_notes"] == "Looks good"
        assert admin_agent.pending_requests[1]["status"] == "approved"
        assert "decided_at" in admin_agent.pending_requests[1]

    def test_process_admin_decision_reject(self, admin_agent):
        """Test rejecting a reservation."""
        # Add a pending request
        admin_agent.add_pending_request(1, {
            "first_name": "John",
            "last_name": "Doe",
            "car_number": "ABC123",
            "start_time": "2024-12-25 14:00",
            "end_time": "2024-12-25 18:00"
        })

        # Reject it
        result = admin_agent.process_admin_decision(
            reservation_id=1,
            decision="rejected",
            admin_notes="Fully booked"
        )

        assert result["success"] is True
        assert result["decision"] == "rejected"
        assert admin_agent.pending_requests[1]["status"] == "rejected"

    def test_process_admin_decision_invalid_decision(self, admin_agent):
        """Test processing with invalid decision."""
        admin_agent.add_pending_request(1, {
            "first_name": "John",
            "last_name": "Doe",
            "car_number": "ABC123",
            "start_time": "2024-12-25 14:00",
            "end_time": "2024-12-25 18:00"
        })

        result = admin_agent.process_admin_decision(
            reservation_id=1,
            decision="maybe"
        )

        assert result["success"] is False
        assert "must be" in result["error"]

    def test_process_admin_decision_not_found(self, admin_agent):
        """Test processing decision for non-existent reservation."""
        result = admin_agent.process_admin_decision(
            reservation_id=999,
            decision="approved"
        )

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_get_reservation_status(self, admin_agent):
        """Test getting reservation status."""
        # Add and approve a request
        admin_agent.add_pending_request(1, {
            "first_name": "John",
            "last_name": "Doe",
            "car_number": "ABC123",
            "start_time": "2024-12-25 14:00",
            "end_time": "2024-12-25 18:00"
        })
        admin_agent.process_admin_decision(1, "approved", "OK")

        status = admin_agent.get_reservation_status(1)

        assert status is not None
        assert status["reservation_id"] == 1
        assert status["status"] == "approved"
        assert status["admin_decision"] == "approved"
        assert status["admin_notes"] == "OK"

    def test_get_reservation_status_not_found(self, admin_agent):
        """Test getting status for non-existent reservation."""
        status = admin_agent.get_reservation_status(999)

        assert status is None

    def test_multiple_reservations(self, admin_agent):
        """Test handling multiple reservations."""
        # Add multiple requests
        for i in range(1, 4):
            admin_agent.add_pending_request(i, {
                "first_name": f"User{i}",
                "last_name": "Test",
                "car_number": f"CAR{i}",
                "start_time": "2024-12-25 14:00",
                "end_time": "2024-12-25 18:00"
            })

        assert len(admin_agent.pending_requests) == 3

        # Check all are in pending requests list
        result = admin_agent.get_pending_requests()
        assert "Reservation ID: 1" in result
        assert "Reservation ID: 2" in result
        assert "Reservation ID: 3" in result
