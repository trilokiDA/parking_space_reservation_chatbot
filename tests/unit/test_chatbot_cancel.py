"""Unit tests for chatbot cancel functionality."""
import pytest
from src.chatbot.chatbot import ParkingChatbot


@pytest.fixture
def chatbot():
    """Create minimal chatbot for testing cancel functionality."""
    bot = ParkingChatbot.__new__(ParkingChatbot)
    # Only initialize what's needed for cancel functionality
    bot.conversation_state = {}
    bot.reservation_data = {}
    return bot


class TestChatbotCancel:
    """Tests for chatbot cancel functionality."""

    def test_is_cancel_request_method(self, chatbot):
        """Test _is_cancel_request method directly."""
        # Test cancel keywords
        assert chatbot._is_cancel_request("cancel") is True
        assert chatbot._is_cancel_request("CANCEL") is True
        assert chatbot._is_cancel_request("I want to cancel") is True
        assert chatbot._is_cancel_request("stop") is True
        assert chatbot._is_cancel_request("exit") is True
        assert chatbot._is_cancel_request("quit") is True
        assert chatbot._is_cancel_request("nevermind") is True
        assert chatbot._is_cancel_request("never mind") is True
        assert chatbot._is_cancel_request("go back") is True
        assert chatbot._is_cancel_request("start over") is True

        # Not cancel requests
        assert chatbot._is_cancel_request("hello") is False
        assert chatbot._is_cancel_request("what are your hours") is False
        assert chatbot._is_cancel_request("book a spot") is False

    def test_reservation_start_message_includes_hint(self, chatbot):
        """Test that reservation start message includes cancel hint."""
        response = chatbot._start_reservation_flow()

        assert "cancel" in response.lower()
        assert "first name" in response.lower()

    def test_is_in_reservation_flow(self, chatbot):
        """Test checking if in reservation flow."""
        # Not in flow initially
        assert chatbot._is_in_reservation_flow() is False

        # Start flow
        chatbot._start_reservation_flow()
        assert chatbot._is_in_reservation_flow() is True

        # Reset flow
        chatbot._reset_reservation_flow()
        assert chatbot._is_in_reservation_flow() is False

    def test_reset_reservation_flow(self, chatbot):
        """Test resetting reservation flow."""
        # Start a reservation
        chatbot.conversation_state = {"flow": "reservation", "step": "car_number"}
        chatbot.reservation_data = {"first_name": "John", "last_name": "Doe"}

        # Reset
        chatbot._reset_reservation_flow()

        # Should clear state
        assert chatbot.conversation_state == {}
        assert chatbot.reservation_data == {}
        assert chatbot._is_in_reservation_flow() is False

    def test_start_reservation_flow_structure(self, chatbot):
        """Test starting reservation flow sets correct state."""
        response = chatbot._start_reservation_flow()

        # Check state is set correctly
        assert chatbot.conversation_state.get("flow") == "reservation"
        assert chatbot.conversation_state.get("step") == "first_name"
        assert chatbot.reservation_data == {}

        # Check response is helpful
        assert len(response) > 0
        assert "cancel" in response.lower()
