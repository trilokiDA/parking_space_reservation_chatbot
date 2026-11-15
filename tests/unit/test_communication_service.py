"""Unit tests for Communication Service."""
import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from src.admin_agent.communication_service import CommunicationService


@pytest.fixture
def communication_service():
    """Create communication service for testing."""
    return CommunicationService(api_url="http://test-api:5000")


class TestCommunicationService:
    """Tests for CommunicationService class."""

    def test_initialization(self, communication_service):
        """Test communication service initialization."""
        assert communication_service.api_url == "http://test-api:5000"
        assert communication_service.timeout == 10

    @patch('requests.post')
    def test_send_reservation_success(self, mock_post, communication_service):
        """Test successfully sending reservation to admin."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "success": True,
            "reservation_id": 1
        }
        mock_post.return_value = mock_response

        reservation_data = {
            "first_name": "John",
            "last_name": "Doe",
            "car_number": "ABC123",
            "start_time": "2024-12-25 14:00",
            "end_time": "2024-12-25 18:00"
        }

        result = communication_service.send_reservation_to_admin(1, reservation_data)

        assert result["success"] is True
        assert "message" in result
        mock_post.assert_called_once()

    @patch('requests.post')
    def test_send_reservation_failure(self, mock_post, communication_service):
        """Test failed reservation submission."""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {
            "success": False,
            "error": "Invalid data"
        }
        mock_post.return_value = mock_response

        reservation_data = {
            "first_name": "John",
            "last_name": "Doe",
            "car_number": "ABC123",
            "start_time": "2024-12-25 14:00",
            "end_time": "2024-12-25 18:00"
        }

        result = communication_service.send_reservation_to_admin(1, reservation_data)

        assert result["success"] is False
        assert "error" in result

    @patch('requests.post')
    def test_send_reservation_connection_error(self, mock_post, communication_service):
        """Test connection error when sending reservation."""
        # Mock connection error
        mock_post.side_effect = requests.exceptions.ConnectionError()

        reservation_data = {
            "first_name": "John",
            "last_name": "Doe",
            "car_number": "ABC123",
            "start_time": "2024-12-25 14:00",
            "end_time": "2024-12-25 18:00"
        }

        result = communication_service.send_reservation_to_admin(1, reservation_data)

        assert result["success"] is False
        assert "unavailable" in result["error"]

    @patch('requests.get')
    def test_check_reservation_status_found(self, mock_get, communication_service):
        """Test checking status of existing reservation."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "status": {
                "reservation_id": 1,
                "status": "approved",
                "admin_decision": "approved"
            }
        }
        mock_get.return_value = mock_response

        status = communication_service.check_reservation_status(1)

        assert status is not None
        assert status["reservation_id"] == 1
        assert status["status"] == "approved"

    @patch('requests.get')
    def test_check_reservation_status_not_found(self, mock_get, communication_service):
        """Test checking status of non-existent reservation."""
        # Mock not found response
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        status = communication_service.check_reservation_status(999)

        assert status is None

    @patch('requests.get')
    def test_check_reservation_status_error(self, mock_get, communication_service):
        """Test error when checking reservation status."""
        # Mock exception
        mock_get.side_effect = Exception("Network error")

        status = communication_service.check_reservation_status(1)

        assert status is None

    @patch('requests.get')
    def test_health_check_healthy(self, mock_get, communication_service):
        """Test health check when service is healthy."""
        # Mock healthy response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        is_healthy = communication_service.health_check()

        assert is_healthy is True

    @patch('requests.get')
    def test_health_check_unhealthy(self, mock_get, communication_service):
        """Test health check when service is down."""
        # Mock exception
        mock_get.side_effect = Exception("Connection refused")

        is_healthy = communication_service.health_check()

        assert is_healthy is False

    @patch('requests.post')
    def test_simulate_admin_decision_approve(self, mock_post, communication_service):
        """Test simulating admin approval."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "decision": "approved"
        }
        mock_post.return_value = mock_response

        result = communication_service.simulate_admin_decision(
            reservation_id=1,
            decision="approved",
            notes="Looks good"
        )

        assert result["success"] is True

    @patch('requests.post')
    def test_simulate_admin_decision_error(self, mock_post, communication_service):
        """Test error in simulating admin decision."""
        # Mock exception
        mock_post.side_effect = Exception("Network error")

        result = communication_service.simulate_admin_decision(
            reservation_id=1,
            decision="approved"
        )

        assert result["success"] is False
        assert "error" in result

    @patch('requests.get')
    def test_get_pending_reservations_success(self, mock_get, communication_service):
        """Test getting pending reservations."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "data": "Pending reservations...",
            "count": 2
        }
        mock_get.return_value = mock_response

        result = communication_service.get_pending_reservations()

        assert result is not None
        assert result["success"] is True
        assert result["count"] == 2

    @patch('requests.get')
    def test_get_pending_reservations_error(self, mock_get, communication_service):
        """Test error getting pending reservations."""
        # Mock exception
        mock_get.side_effect = Exception("Network error")

        result = communication_service.get_pending_reservations()

        assert result is None
