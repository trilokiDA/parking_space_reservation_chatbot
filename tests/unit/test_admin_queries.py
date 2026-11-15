"""Unit tests for admin query detection and handling."""
import pytest
from unittest.mock import Mock, MagicMock
from src.chatbot.chatbot import ParkingChatbot
from src.config.settings import Settings


@pytest.fixture
def mock_settings():
    """Create mock settings."""
    settings = Mock(spec=Settings)
    settings.database_url = "sqlite:///test.db"
    settings.embedding_model = "all-MiniLM-L6-v2"
    settings.openai_api_key = "test-key"
    settings.groq_api_key = None
    settings.vector_store_path = "test_vectors"
    settings.chunk_size = 500
    settings.chunk_overlap = 50
    settings.retrieval_k = 3
    settings.llm_model = "gpt-3.5-turbo"
    settings.llm_temperature = 0.7
    settings.max_tokens = 500
    settings.admin_api_url = "http://localhost:8000"
    settings.get_active_provider = Mock(return_value="openai")
    settings.get_active_api_key = Mock(return_value="test-key")
    return settings


class TestAdminQueryDetection:
    """Test admin query detection."""

    def test_is_admin_query_pending_reservations(self):
        """Test detection of pending reservations query."""
        test_cases = [
            "Show me all pending reservations",
            "Show all pending reservations",
            "List pending reservations",
            "What are the pending reservations?",
            "pending reservations",
        ]

        # We need a minimal chatbot instance just to test the method
        # In a real scenario, you'd mock all dependencies
        for test_input in test_cases:
            # Create a minimal instance for testing
            chatbot = ParkingChatbot.__new__(ParkingChatbot)
            chatbot.conversation_state = {}

            result = chatbot._is_admin_query(test_input)
            assert result, f"Should detect '{test_input}' as admin query"

    def test_is_admin_query_status_check(self):
        """Test detection of status check queries."""
        test_cases = [
            "Check status of reservation 2",
            "What is the status of reservation 5",
            "Reservation status 10",
            "Show me reservation 3 status",
        ]

        for test_input in test_cases:
            chatbot = ParkingChatbot.__new__(ParkingChatbot)
            chatbot.conversation_state = {}

            result = chatbot._is_admin_query(test_input)
            assert result, f"Should detect '{test_input}' as admin query"

    def test_is_not_admin_query(self):
        """Test that non-admin queries are not detected as admin queries."""
        test_cases = [
            "I want to make a reservation",
            "What are your hours?",
            "How much does parking cost?",
            "I need parking",
            "Book a spot for me",
        ]

        for test_input in test_cases:
            chatbot = ParkingChatbot.__new__(ParkingChatbot)
            chatbot.conversation_state = {}

            result = chatbot._is_admin_query(test_input)
            assert not result, f"Should NOT detect '{test_input}' as admin query"


class TestReservationRequestDetection:
    """Test reservation request detection."""

    def test_is_reservation_request(self):
        """Test detection of reservation requests."""
        test_cases = [
            "I want to make a reservation",
            "Make a reservation for me",
            "I need to book parking",
            "Book a spot",
            "I need parking",
            "Reserve a spot for tomorrow",
        ]

        for test_input in test_cases:
            chatbot = ParkingChatbot.__new__(ParkingChatbot)
            chatbot.conversation_state = {}

            result = chatbot._is_reservation_request(test_input)
            assert result, f"Should detect '{test_input}' as reservation request"

    def test_is_not_reservation_request(self):
        """Test that admin queries are not detected as reservation requests."""
        test_cases = [
            "Show me all pending reservations",
            "Check status of reservation 2",
            "List all reservations",
            "What are your hours?",
        ]

        for test_input in test_cases:
            chatbot = ParkingChatbot.__new__(ParkingChatbot)
            chatbot.conversation_state = {}

            result = chatbot._is_reservation_request(test_input)
            assert not result, f"Should NOT detect '{test_input}' as reservation request"


class TestFlowPriority:
    """Test that admin queries take priority over reservation flow."""

    def test_admin_query_exits_reservation_flow(self):
        """Test that admin query exits active reservation flow."""
        chatbot = ParkingChatbot.__new__(ParkingChatbot)
        chatbot.conversation_state = {"flow": "reservation", "step": "first_name"}
        chatbot.reservation_data = {}

        # Admin query should be detected
        assert chatbot._is_admin_query("Show pending reservations")

        # User is in reservation flow
        assert chatbot._is_in_reservation_flow()

        # After processing admin query, should exit flow
        # (This would require mocking database and other dependencies)

    def test_cancel_exits_reservation_flow(self):
        """Test that cancel command exits reservation flow."""
        chatbot = ParkingChatbot.__new__(ParkingChatbot)
        chatbot.conversation_state = {"flow": "reservation", "step": "car_number"}
        chatbot.reservation_data = {"first_name": "John", "last_name": "Doe"}

        # Should detect cancel
        assert chatbot._is_cancel_request("cancel")
        assert chatbot._is_cancel_request("I want to cancel")

        # Should be in flow before reset
        assert chatbot._is_in_reservation_flow()

        # Reset should clear state
        chatbot._reset_reservation_flow()
        assert not chatbot._is_in_reservation_flow()
        assert chatbot.reservation_data == {}


class TestCancelDetection:
    """Test cancel/exit request detection."""

    def test_is_cancel_request(self):
        """Test detection of cancel requests."""
        test_cases = [
            "cancel",
            "stop",
            "exit",
            "quit",
            "nevermind",
            "never mind",
            "go back",
            "start over",
            "I want to cancel",
            "Can I stop this?",
        ]

        for test_input in test_cases:
            chatbot = ParkingChatbot.__new__(ParkingChatbot)

            result = chatbot._is_cancel_request(test_input)
            assert result, f"Should detect '{test_input}' as cancel request"

    def test_is_not_cancel_request(self):
        """Test that normal messages are not cancel requests."""
        test_cases = [
            "I want to make a reservation",
            "John",
            "ABC123",
            "What are your hours?",
        ]

        for test_input in test_cases:
            chatbot = ParkingChatbot.__new__(ParkingChatbot)

            result = chatbot._is_cancel_request(test_input)
            assert not result, f"Should NOT detect '{test_input}' as cancel request"
