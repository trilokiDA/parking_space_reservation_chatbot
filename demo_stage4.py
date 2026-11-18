"""
Demo script for Stage 4: LangGraph Orchestration
Demonstrates the complete workflow integration.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config.settings import Settings
from src.orchestration.workflow_graph import ReservationOrchestrator
from src.database.db_manager import DatabaseManager

# Load environment variables
load_dotenv()


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def demo_workflow_architecture():
    """Demonstrate the workflow architecture."""
    print_section("STAGE 4: LANGGRAPH WORKFLOW ARCHITECTURE")

    architecture = """
    ┌─────────────────────────────────────────────────────────────────┐
    │                    LangGraph Orchestration                      │
    │                                                                 │
    │   User Input → RAG Chatbot → Admin Agent → MCP Server          │
    │      ↓            ↓              ↓             ↓                │
    │   Stage 1      Stage 1        Stage 2       Stage 3            │
    │   Vector DB    SQL DB         Decision      File Write         │
    └─────────────────────────────────────────────────────────────────┘

    Workflow Stages:
    1. 💬 User Interaction    - RAG chatbot processes queries
    2. ⏳ Awaiting Approval   - Admin reviews reservation
    3. ⚙️  Processing          - MCP server writes to file
    4. ✅ Completed           - User notified of success
    5. ❌ Rejected            - User notified of rejection
    """
    print(architecture)


def demo_information_query(orchestrator):
    """Demo: Simple information query."""
    print_section("DEMO 1: Information Query")

    print("Query: 'What are your operating hours?'\n")

    result = orchestrator.process_user_input(
        "What are your operating hours?",
        thread_id="demo_info"
    )

    print(f"Response: {result.get('chatbot_response', 'No response')}\n")
    print(f"Workflow Stage: {result.get('current_stage', 'Unknown')}")

    return result


def demo_reservation_creation(orchestrator, db_manager):
    """Demo: Create a reservation."""
    print_section("DEMO 2: Reservation Creation")

    # Simulate reservation creation by directly adding to database
    # (In real usage, chatbot collects this info interactively)
    print("Creating a test reservation...")

    start_time = datetime.now() + timedelta(days=1)
    end_time = start_time + timedelta(hours=4)

    reservation_id = db_manager.create_reservation(
        first_name="Demo",
        last_name="User",
        car_number="DEMO123",
        start_time=start_time,
        end_time=end_time
    )

    print(f"✓ Reservation created with ID: {reservation_id}")
    print(f"  Name: Demo User")
    print(f"  Car: DEMO123")
    print(f"  Period: {start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')}")
    print(f"  Status: Pending admin approval")

    return reservation_id


def demo_status_check(orchestrator, reservation_id):
    """Demo: Check reservation status."""
    print_section("DEMO 3: Status Check")

    print(f"Checking status of reservation {reservation_id}...\n")

    status = orchestrator.get_workflow_status(reservation_id)

    if status.get("found"):
        print(f"✓ Reservation found!")
        print(f"  ID: {status['reservation_id']}")
        print(f"  Status: {status['status']}")
        print(f"  Name: {status['first_name']} {status['last_name']}")
        print(f"  Car: {status['car_number']}")
        if status.get('admin_notes'):
            print(f"  Admin Notes: {status['admin_notes']}")
    else:
        print(f"✗ Reservation not found")

    return status


def demo_approval_workflow(orchestrator, db_manager, reservation_id):
    """Demo: Admin approval workflow."""
    print_section("DEMO 4: Admin Approval")

    print(f"Simulating admin approval for reservation {reservation_id}...\n")

    # Simulate admin approval
    success = db_manager.update_reservation_status(
        reservation_id,
        "approved",
        "Demo approval - looks good!"
    )

    if success:
        print("✓ Admin approved the reservation")
        print("  Notes: Demo approval - looks good!")

        # Check status again
        reservation = db_manager.get_reservation(reservation_id)
        print(f"  Updated Status: {reservation.status}")
    else:
        print("✗ Failed to update reservation status")


def demo_mcp_processing(orchestrator, db_manager, reservation_id):
    """Demo: MCP server processing."""
    print_section("DEMO 5: MCP Server Processing")

    print(f"Processing approved reservation {reservation_id} through MCP server...\n")

    # Get reservation data
    reservation = db_manager.get_reservation(reservation_id)

    if not reservation:
        print("✗ Reservation not found")
        return

    # Simulate MCP processing through orchestrator
    state = {
        "reservation_data": {
            "id": reservation.id,
            "first_name": reservation.first_name,
            "last_name": reservation.last_name,
            "car_number": reservation.car_number,
            "start_time": reservation.start_time,
            "end_time": reservation.end_time,
            "admin_notes": reservation.admin_notes
        },
        "current_stage": "processing"
    }

    result = orchestrator._mcp_processing_node(state)

    if result.get("current_stage") == "completed":
        print("✓ Reservation successfully written to MCP server")
        print("  File: data/confirmed_reservations.txt")
        print(f"  Status: {result.get('current_stage')}")
    else:
        error = result.get("error_message", "Unknown error")
        print(f"✗ MCP processing failed: {error}")
        print("  Note: Make sure MCP server is running (python run_mcp_server.py)")


def demo_complete_workflow(orchestrator, db_manager):
    """Demo: Complete end-to-end workflow."""
    print_section("DEMO 6: Complete Workflow")

    print("Running complete workflow simulation...\n")

    # 1. Create reservation
    print("Step 1: Creating reservation...")
    start_time = datetime.now() + timedelta(days=2)
    end_time = start_time + timedelta(hours=3)

    res_id = db_manager.create_reservation(
        first_name="Complete",
        last_name="Test",
        car_number="FULL123",
        start_time=start_time,
        end_time=end_time
    )
    print(f"  ✓ Created reservation {res_id}")

    # 2. Check initial status
    print("\nStep 2: Checking initial status...")
    status = orchestrator.get_workflow_status(res_id)
    print(f"  ✓ Status: {status.get('status')}")

    # 3. Simulate admin approval
    print("\nStep 3: Admin approval...")
    db_manager.update_reservation_status(
        res_id,
        "approved",
        "Complete workflow test - approved"
    )
    print(f"  ✓ Approved")

    # 4. Check final status
    print("\nStep 4: Checking final status...")
    final_status = orchestrator.get_workflow_status(res_id)
    print(f"  ✓ Final Status: {final_status.get('status')}")
    print(f"  ✓ Admin Notes: {final_status.get('admin_notes')}")

    print("\n✓ Complete workflow executed successfully!")


def demo_statistics(orchestrator):
    """Demo: View system statistics."""
    print_section("DEMO 7: System Statistics")

    try:
        stats = orchestrator.chatbot.evaluator.get_statistics()

        print("Performance Metrics:")
        print("-" * 50)
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"  {key:25}: {value:.3f}")
            else:
                print(f"  {key:25}: {value}")
    except Exception as e:
        print(f"Could not retrieve statistics: {e}")


def main():
    """Main demo execution."""
    print("""
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║   Intelligent Parking Reservation System                      ║
║   Stage 4: LangGraph Orchestration Demo                       ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝
""")

    try:
        # Initialize components
        print("Initializing system...")
        settings = Settings()
        settings.database_url = "sqlite:///demo_stage4.db"

        db_manager = DatabaseManager(settings.database_url)
        orchestrator = ReservationOrchestrator(settings)

        print("✓ System initialized\n")

        # Run demos
        demo_workflow_architecture()

        input("Press Enter to continue to Demo 1...")
        demo_information_query(orchestrator)

        input("\nPress Enter to continue to Demo 2...")
        reservation_id = demo_reservation_creation(orchestrator, db_manager)

        input("\nPress Enter to continue to Demo 3...")
        demo_status_check(orchestrator, reservation_id)

        input("\nPress Enter to continue to Demo 4...")
        demo_approval_workflow(orchestrator, db_manager, reservation_id)

        input("\nPress Enter to continue to Demo 5...")
        demo_mcp_processing(orchestrator, db_manager, reservation_id)

        input("\nPress Enter to continue to Demo 6...")
        demo_complete_workflow(orchestrator, db_manager)

        input("\nPress Enter to continue to Demo 7...")
        demo_statistics(orchestrator)

        print_section("DEMO COMPLETE")
        print("All Stage 4 features demonstrated successfully!")
        print("\nTo run the full system, use: python orchestrated_main.py")
        print("To run tests, use: pytest tests/ -v")

    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n✗ Error during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
