"""Test script for admin query detection."""
from src.chatbot.chatbot import ParkingChatbot
from src.config.settings import get_settings
from dotenv import load_dotenv

load_dotenv()

def test_admin_queries():
    """Test admin query detection and handling."""
    print("=" * 60)
    print("Testing Admin Query Detection")
    print("=" * 60)

    settings = get_settings()
    chatbot = ParkingChatbot(settings)

    # Test cases
    test_cases = [
        "Show me all pending reservations",
        "Check status of reservation 2",
        "What are pending reservations?",
        "I want to make a reservation",
        "List all reservations",
    ]

    for i, test_input in enumerate(test_cases, 1):
        print(f"\n[Test {i}] User: {test_input}")

        # Check detection
        is_admin = chatbot._is_admin_query(test_input)
        is_reservation = chatbot._is_reservation_request(test_input)

        print(f"  -> Is admin query: {is_admin}")
        print(f"  -> Is reservation request: {is_reservation}")

        # Get response
        response = chatbot.process_message(test_input)
        print(f"  -> Response: {response[:100]}...")

if __name__ == "__main__":
    test_admin_queries()
