"""
Main entry point for Stage 4: LangGraph-orchestrated parking reservation system.
Complete integration of all components via LangGraph workflow.
"""
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config.settings import Settings
from src.orchestration.workflow_graph import ReservationOrchestrator

# Load environment variables
load_dotenv()

# Setup logging - INFO to file, WARNING to console
file_handler = logging.FileHandler('orchestrated_chatbot.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)  # Only show warnings and errors in console
console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, console_handler]
)

# Suppress INFO logs from external libraries
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)
logging.getLogger('openai').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def print_banner():
    """Print welcome banner."""
    banner = """
╔════════════════════════════════════════════════════════════════╗
║   Intelligent Parking Reservation System - Stage 4             ║
║   LangGraph Orchestrated Workflow                              ║
╚════════════════════════════════════════════════════════════════╝

This system orchestrates:
  1. RAG Chatbot (User Interaction)
  2. Admin Approval Agent (Human-in-the-Loop)
  3. MCP Server (Confirmed Reservation Processing)

Commands:
  - Ask questions about parking
  - Make reservations: "I want to make a reservation"
  - Check status: "Check status of reservation [ID]"
  - Type 'help' for more information
  - Type 'workflow' to see workflow status
  - Type 'quit' or 'exit' to end the session
"""
    print(banner)


def print_help():
    """Print help information."""
    help_text = """
═══════════════════ HELP ═══════════════════

📋 Available Commands:
  help      - Show this help message
  workflow  - Display workflow status information
  stats     - Show performance statistics
  quit/exit - Exit the chatbot

💬 Example Queries:
  "What are your operating hours?"
  "How much does parking cost?"
  "I want to make a reservation"
  "Check status of reservation 1"

🔄 Workflow Stages:
  1. User Interaction - Chat with RAG agent
  2. Awaiting Approval - Admin reviews request
  3. Processing - MCP server writes confirmed data
  4. Completed - Reservation confirmed and saved

════════════════════════════════════════════
"""
    print(help_text)


def print_workflow_info():
    """Print workflow architecture information."""
    workflow_info = """
═══════════════ WORKFLOW ARCHITECTURE ═══════════════

┌─────────────────┐
│  User Input     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ RAG Chatbot     │ ◄── Stage 1: Information retrieval & interaction
│ (LangChain)     │
└────────┬────────┘
         │
         ▼
    Is Reservation?
    /           \\
   No           Yes
   │             │
   │             ▼
   │    ┌─────────────────┐
   │    │ Admin Agent     │ ◄── Stage 2: Human-in-the-loop approval
   │    │ (LangChain)     │
   │    └────────┬────────┘
   │             │
   │             ▼
   │        Approved?
   │        /         \\
   │      No          Yes
   │      │            │
   │      │            ▼
   │      │    ┌─────────────────┐
   │      │    │ MCP Server      │ ◄── Stage 3: File-based storage
   │      │    │ (FastAPI)       │
   │      │    └────────┬────────┘
   │      │             │
   │      ▼             ▼
   │  ┌─────────────────────┐
   └─►│ User Notification   │
      └─────────────────────┘

LangGraph manages state transitions and orchestrates all components.

════════════════════════════════════════════════════
"""
    print(workflow_info)


def main():
    """Main application loop."""
    try:
        # Load settings
        logger.info("Loading application settings...")
        settings = Settings()

        # Initialize orchestrator
        logger.info("Initializing LangGraph orchestrator...")
        print("🔄 Initializing system components...")
        orchestrator = ReservationOrchestrator(settings)
        print("✅ System ready!\n")

        # Print banner
        print_banner()

        # Main loop
        thread_id = "main_session"

        while True:
            try:
                # Get user input
                user_input = input("\n🗣️  You: ").strip()

                # Handle empty input
                if not user_input:
                    continue

                # Handle commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Thank you for using our parking reservation system. Goodbye!")
                    break

                if user_input.lower() == 'help':
                    print_help()
                    continue

                if user_input.lower() == 'workflow':
                    print_workflow_info()
                    continue

                if user_input.lower() == 'stats':
                    # Show statistics from evaluator
                    stats = orchestrator.chatbot.evaluator.get_statistics()
                    print("\n" + "="*60)
                    print("📊 PERFORMANCE STATISTICS")
                    print("="*60)
                    for key, value in stats.items():
                        if isinstance(value, float):
                            print(f"{key}: {value:.3f}")
                        else:
                            print(f"{key}: {value}")
                    print("="*60)
                    continue

                # Process through orchestrator
                print("\n🔄 Processing through workflow...\n")

                result = orchestrator.process_user_input(user_input, thread_id)

                # Display response
                response = result.get("chatbot_response", "")
                if response:
                    print(f"🤖 Bot: {response}")

                # Show workflow status
                current_stage = result.get("current_stage", "")
                if current_stage:
                    stage_emoji = {
                        "user_interaction": "💬",
                        "awaiting_approval": "⏳",
                        "processing": "⚙️",
                        "completed": "✅",
                        "rejected": "❌",
                        "error": "⚠️"
                    }
                    emoji = stage_emoji.get(current_stage, "ℹ️")
                    print(f"\n{emoji} Workflow Stage: {current_stage.replace('_', ' ').title()}")

                # Show any errors
                error = result.get("error_message")
                if error:
                    print(f"⚠️ Error: {error}")

                # Show reservation info if available
                reservation_id = result.get("reservation_id")
                if reservation_id and current_stage == "awaiting_approval":
                    print(f"\n📋 Reservation ID: {reservation_id}")
                    print("💡 Tip: An administrator will review your request.")
                    print("     Check status with: 'Check status of reservation {}'".format(reservation_id))

            except KeyboardInterrupt:
                print("\n\n👋 Interrupted. Goodbye!")
                break

            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                print(f"\n⚠️ An error occurred: {e}")
                print("Please try again or type 'help' for assistance.")

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n❌ Fatal error: {e}")
        print("Please check your configuration and try again.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
