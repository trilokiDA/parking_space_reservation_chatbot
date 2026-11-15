"""Admin interface CLI for managing reservation requests."""
import os
import logging
from dotenv import load_dotenv
from src.config.settings import get_settings
from src.admin_agent.admin_agent import AdminAgent
from src.admin_agent.admin_api import AdminAPI

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_welcome():
    """Print welcome message."""
    print("\n" + "=" * 60)
    print("    ADMIN RESERVATION MANAGEMENT INTERFACE")
    print("=" * 60)
    print("\nAvailable Commands:")
    print("  • 'pending' - View all pending reservations")
    print("  • 'details <id>' - View details of reservation ID")
    print("  • 'approve <id>' - Approve reservation ID")
    print("  • 'reject <id>' - Reject reservation ID")
    print("  • 'status <id>' - Check status of reservation ID")
    print("  • 'query <question>' - Ask the AI agent a question")
    print("  • 'help' - Show this help message")
    print("  • 'quit' - Exit the interface")
    print("=" * 60 + "\n")


def process_command(command: str, admin_agent: AdminAgent):
    """Process admin command.

    Args:
        command: User command
        admin_agent: AdminAgent instance
    """
    parts = command.strip().split(maxsplit=1)

    if not parts:
        return

    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    if cmd == "pending":
        result = admin_agent.get_pending_requests()
        print(f"\n{result}\n")

    elif cmd == "details":
        try:
            res_id = int(args)
            result = admin_agent.get_request_details(res_id)
            print(f"\n{result}\n")
        except ValueError:
            print("\n❌ Invalid reservation ID. Use: details <id>\n")

    elif cmd == "approve":
        try:
            res_id = int(args)
            notes = input("Add notes (optional, press Enter to skip): ").strip()
            result = admin_agent.process_admin_decision(
                reservation_id=res_id,
                decision="approved",
                admin_notes=notes or None
            )
            if result.get("success"):
                print(f"\n✓ Reservation {res_id} approved successfully!\n")
            else:
                print(f"\n❌ Error: {result.get('error')}\n")
        except ValueError:
            print("\n❌ Invalid reservation ID. Use: approve <id>\n")

    elif cmd == "reject":
        try:
            res_id = int(args)
            notes = input("Add reason for rejection (optional): ").strip()
            result = admin_agent.process_admin_decision(
                reservation_id=res_id,
                decision="rejected",
                admin_notes=notes or None
            )
            if result.get("success"):
                print(f"\n✓ Reservation {res_id} rejected.\n")
            else:
                print(f"\n❌ Error: {result.get('error')}\n")
        except ValueError:
            print("\n❌ Invalid reservation ID. Use: reject <id>\n")

    elif cmd == "status":
        try:
            res_id = int(args)
            status = admin_agent.get_reservation_status(res_id)
            if status:
                print(f"\n📊 Reservation {res_id} Status:")
                print(f"  Status: {status.get('status')}")
                print(f"  Admin Decision: {status.get('admin_decision')}")
                if status.get('admin_notes'):
                    print(f"  Notes: {status.get('admin_notes')}")
                if status.get('decided_at'):
                    print(f"  Decided At: {status.get('decided_at')}")
                print()
            else:
                print(f"\n❌ Reservation {res_id} not found\n")
        except ValueError:
            print("\n❌ Invalid reservation ID. Use: status <id>\n")

    elif cmd == "query":
        if not args:
            print("\n❌ Please provide a question. Use: query <your question>\n")
            return
        result = admin_agent.query_admin(args)
        print(f"\n🤖 Agent Response:\n{result}\n")

    elif cmd == "help":
        print_welcome()

    else:
        print(f"\n❌ Unknown command: {cmd}. Type 'help' for available commands.\n")


def main():
    """Run the admin interface."""
    # Load environment variables
    load_dotenv()

    # Check for API key
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("GROQ_API_KEY"):
        print("\n❌ Error: No API key found!")
        print("Please create a .env file with either OPENAI_API_KEY or GROQ_API_KEY.")
        return

    try:
        # Initialize settings and admin agent
        logger.info("Initializing admin agent...")
        settings = get_settings()
        admin_agent = AdminAgent(settings)

        # Start the API server
        logger.info("Starting admin API server...")
        admin_api = AdminAPI(
            admin_agent=admin_agent,
            host="127.0.0.1",
            port=settings.admin_api_port
        )
        admin_api.start(threaded=True)

        print("\n✓ Admin API server started successfully")
        print(f"  URL: http://127.0.0.1:{settings.admin_api_port}")
        print(f"  Health check: http://127.0.0.1:{settings.admin_api_port}/health\n")

        # Print welcome message
        print_welcome()

        # Main command loop
        while True:
            try:
                command = input("Admin> ").strip()

                if command.lower() in ['quit', 'exit']:
                    print("\nGoodbye! 👋\n")
                    break

                if not command:
                    continue

                process_command(command, admin_agent)

            except KeyboardInterrupt:
                print("\n\nExiting... Goodbye! 👋\n")
                break
            except Exception as e:
                logger.error(f"Error processing command: {e}")
                print(f"\n❌ An error occurred: {e}\n")

    except Exception as e:
        logger.error(f"Failed to initialize admin interface: {e}")
        print(f"\n❌ Error: {e}\n")


if __name__ == "__main__":
    main()
