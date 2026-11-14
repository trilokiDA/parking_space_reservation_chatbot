"""Main entry point for the parking chatbot application."""
import os
import logging
from dotenv import load_dotenv
from src.config.settings import get_settings
from src.chatbot.chatbot import ParkingChatbot

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_welcome():
    """Print welcome message."""
    print("\n" + "=" * 60)
    print("    INTELLIGENT PARKING RESERVATION CHATBOT")
    print("=" * 60)
    print("\nWelcome! I can help you with:")
    print("  • General parking information")
    print("  • Availability and pricing")
    print("  • Making reservations")
    print("  • Answering your questions")
    print("\nType 'quit' or 'exit' to end the conversation.")
    print("Type 'help' for assistance.")
    print("=" * 60 + "\n")


def print_help():
    """Print help message."""
    print("\n" + "=" * 60)
    print("HELP - What you can ask:")
    print("=" * 60)
    print("\nInformation Queries:")
    print("  • What are your hours?")
    print("  • How much does parking cost?")
    print("  • Are there available spaces?")
    print("  • Where is the parking located?")
    print("  • Do you have EV charging?")
    print("\nReservations:")
    print("  • I want to make a reservation")
    print("  • I need to book a parking space")
    print("  • Reserve a spot for tomorrow")
    print("\nCommands:")
    print("  • 'help' - Show this help message")
    print("  • 'stats' - Show performance statistics")
    print("  • 'quit' or 'exit' - Exit the chatbot")
    print("=" * 60 + "\n")


def main():
    """Run the chatbot application."""
    # Load environment variables
    load_dotenv()

    # Check for at least one API key
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("GROQ_API_KEY"):
        print("\n❌ Error: No API key found!")
        print("Please create a .env file with either OPENAI_API_KEY or GROQ_API_KEY.")
        print("See .env.example for the required format.\n")
        return

    try:
        # Initialize settings and chatbot
        logger.info("Initializing chatbot...")
        settings = get_settings()
        chatbot = ParkingChatbot(settings)

        # Print welcome message
        print_welcome()

        # Main conversation loop
        while True:
            try:
                # Get user input
                user_input = input("You: ").strip()

                # Check for commands
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("\nThank you for using our parking chatbot. Goodbye! 👋\n")
                    break

                if user_input.lower() == 'help':
                    print_help()
                    continue

                if user_input.lower() == 'stats':
                    evaluator = chatbot.get_evaluator()
                    stats = evaluator.get_statistics()
                    if stats:
                        print("\n" + evaluator.generate_report())
                    else:
                        print("\nNo statistics available yet. Have a conversation first!\n")
                    continue

                if not user_input:
                    continue

                # Process message
                response = chatbot.process_message(user_input)

                # Print response
                print(f"\nBot: {response}\n")

            except KeyboardInterrupt:
                print("\n\nExiting... Goodbye! 👋\n")
                break
            except Exception as e:
                logger.error(f"Error in conversation loop: {e}")
                print("\n❌ An error occurred. Please try again.\n")

    except Exception as e:
        logger.error(f"Failed to initialize chatbot: {e}")
        print(f"\n❌ Error: {e}")
        print("\nPlease ensure:")
        print("  1. You have run: pip install -r requirements.txt")
        print("  2. You have created a .env file with your API key (OPENAI_API_KEY or GROQ_API_KEY)")
        print("  3. You have initialized the vector store: python init_vectorstore.py\n")


if __name__ == "__main__":
    main()
