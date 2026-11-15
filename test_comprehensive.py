"""Comprehensive test showing the fix working."""
from src.chatbot.chatbot import ParkingChatbot
from src.config.settings import get_settings
from dotenv import load_dotenv

load_dotenv()

def print_interaction(user_msg, bot_response, description=""):
    """Print a conversation interaction nicely formatted."""
    if description:
        print(f"\n>>> {description}")
    print(f"You: {user_msg}")
    print(f"Bot: {bot_response}\n")
    print("-" * 80)

def test_comprehensive():
    """Test comprehensive scenarios."""
    print("=" * 80)
    print("COMPREHENSIVE TEST: Admin Queries vs Reservation Flow")
    print("=" * 80)

    settings = get_settings()
    chatbot = ParkingChatbot(settings)

    # Scenario 1: Admin query does NOT start reservation flow
    print("\n🔍 SCENARIO 1: Admin queries should NOT trigger reservation flow")
    print("=" * 80)

    response = chatbot.process_message("Show me all pending reservations")
    print_interaction("Show me all pending reservations", response, "User asks about pending reservations")
    assert "Pending Reservations" in response or "no pending reservations" in response.lower()
    assert not chatbot._is_in_reservation_flow(), "Should NOT be in reservation flow"

    response = chatbot.process_message("Check status of reservation 2")
    print_interaction("Check status of reservation 2", response, "User checks specific reservation status")
    assert "Status:" in response or "not found" in response.lower()
    assert not chatbot._is_in_reservation_flow(), "Should NOT be in reservation flow"

    # Scenario 2: Starting a reservation flow properly
    print("\n🔍 SCENARIO 2: Making a new reservation should start flow")
    print("=" * 80)

    response = chatbot.process_message("I want to make a reservation")
    print_interaction("I want to make a reservation", response, "User wants to make a new reservation")
    assert "first name" in response.lower()
    assert chatbot._is_in_reservation_flow(), "Should be in reservation flow"

    # Scenario 3: Admin query interrupts and exits reservation flow
    print("\n🔍 SCENARIO 3: Admin query should interrupt reservation flow")
    print("=" * 80)

    response = chatbot.process_message("Actually, show me all pending reservations")
    print_interaction("Actually, show me all pending reservations", response,
                     "User interrupts reservation to check pending")
    assert "Pending Reservations" in response or "no pending reservations" in response.lower()
    assert not chatbot._is_in_reservation_flow(), "Should have EXITED reservation flow"

    # Scenario 4: Cancel works in reservation flow
    print("\n🔍 SCENARIO 4: Cancel should work in reservation flow")
    print("=" * 80)

    chatbot.process_message("I want to book a spot")
    assert chatbot._is_in_reservation_flow(), "Should be in reservation flow"

    response = chatbot.process_message("cancel")
    print_interaction("cancel", response, "User cancels reservation")
    assert "cancelled" in response.lower()
    assert not chatbot._is_in_reservation_flow(), "Should have exited reservation flow"

    # Scenario 5: Complete reservation flow without interruption
    print("\n🔍 SCENARIO 5: Complete reservation flow")
    print("=" * 80)

    responses = []

    msg = "I need parking"
    resp = chatbot.process_message(msg)
    print_interaction(msg, resp, "Start reservation")
    assert chatbot._is_in_reservation_flow()

    msg = "John"
    resp = chatbot.process_message(msg)
    print_interaction(msg, resp, "Provide first name")
    assert chatbot._is_in_reservation_flow()

    msg = "Doe"
    resp = chatbot.process_message(msg)
    print_interaction(msg, resp, "Provide last name")
    assert chatbot._is_in_reservation_flow()

    msg = "XYZ9999"
    resp = chatbot.process_message(msg)
    print_interaction(msg, resp, "Provide car number")
    assert chatbot._is_in_reservation_flow()

    msg = "2026-12-25 10:00"
    resp = chatbot.process_message(msg)
    print_interaction(msg, resp, "Provide start time")
    assert chatbot._is_in_reservation_flow()

    msg = "2026-12-25 18:00"
    resp = chatbot.process_message(msg)
    print_interaction(msg, resp, "Provide end time")
    assert not chatbot._is_in_reservation_flow(), "Should have completed and exited"
    assert "Reservation created" in resp or "Reservation ID" in resp

    print("\n✅ ALL TESTS PASSED!")
    print("=" * 80)

if __name__ == "__main__":
    test_comprehensive()
