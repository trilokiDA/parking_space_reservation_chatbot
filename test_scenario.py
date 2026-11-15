"""Test the exact scenario from the user's pasted conversation."""
from src.chatbot.chatbot import ParkingChatbot
from src.config.settings import get_settings
from dotenv import load_dotenv

load_dotenv()

def test_scenario():
    """Test the scenario where user asks about reservations during reservation flow."""
    print("=" * 80)
    print("TESTING SCENARIO: Admin queries interrupting reservation flow")
    print("=" * 80)

    settings = get_settings()
    chatbot = ParkingChatbot(settings)

    # Simulate the conversation
    conversations = [
        ("You", "Show me all pending reservations"),
        ("You", "Triloki"),
        ("You", "Gupta"),
        ("You", "abcd1234"),
        ("You", "Check status of reservation 2"),
    ]

    print("\n" + "=" * 80)
    print("CONVERSATION:")
    print("=" * 80 + "\n")

    for speaker, message in conversations:
        print(f"{speaker}: {message}")
        response = chatbot.process_message(message)
        print(f"\nBot: {response}\n")
        print("-" * 80 + "\n")

if __name__ == "__main__":
    test_scenario()
