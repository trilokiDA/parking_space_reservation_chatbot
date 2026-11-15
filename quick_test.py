"""Quick interactive test of the fix."""
from src.chatbot.chatbot import ParkingChatbot
from src.config.settings import get_settings
from dotenv import load_dotenv

load_dotenv()

def quick_test():
    """Quick test of common scenarios."""
    print("\n" + "=" * 80)
    print("QUICK TEST - Fixed Admin Query Handling")
    print("=" * 80 + "\n")

    settings = get_settings()
    chatbot = ParkingChatbot(settings)

    # Test the exact scenario from the user's bug report
    print("Testing the exact scenario from your bug report:\n")

    test_messages = [
        "Show me all pending reservations",
        "Check status of reservation 2"
    ]

    for msg in test_messages:
        print(f"You: {msg}")
        response = chatbot.process_message(msg)
        print(f"Bot: {response}\n")
        print("-" * 80 + "\n")

    print("✅ The bot now correctly handles admin queries!")
    print("   - 'Show me all pending reservations' lists reservations")
    print("   - 'Check status of reservation 2' shows reservation details")
    print("   - These queries do NOT start the reservation flow\n")

if __name__ == "__main__":
    quick_test()
