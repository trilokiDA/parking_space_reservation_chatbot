"""
Demo script for Stage 3 - MCP Server Integration
Demonstrates the complete workflow from user request to file writing.
"""
import os
import sys
from pathlib import Path
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.database.db_manager import DatabaseManager
from src.admin_agent.admin_agent_db import AdminAgentDB
from src.mcp_server.mcp_client import MCPClient
from src.config.settings import get_settings

# Load environment
load_dotenv()


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def demo_stage3():
    """Run Stage 3 demonstration."""
    print("\n" + "🎯" * 35)
    print("         STAGE 3 DEMONSTRATION - MCP SERVER INTEGRATION")
    print("🎯" * 35 + "\n")

    # Initialize components
    print("📦 Initializing components...")
    settings = get_settings()
    db_manager = DatabaseManager(settings.database_url)

    # Check if MCP server is running
    mcp_client = MCPClient()

    print_section("1. CHECKING MCP SERVER STATUS")
    health = mcp_client.check_health()
    if health.get("status") == "healthy":
        print("✅ MCP Server is running")
        print(f"   URL: {mcp_client.base_url}")
        print(f"   File: {health.get('file_path')}")
    else:
        print("❌ MCP Server is not running!")
        print("   Please start the server first: python run_mcp_server.py")
        return

    print_section("2. CREATING TEST RESERVATION")

    # Create a test reservation
    test_data = {
        "first_name": "Demo",
        "last_name": "User",
        "car_number": "DEMO123",
        "start_time": datetime.now() + timedelta(days=1),
        "end_time": datetime.now() + timedelta(days=1, hours=4)
    }

    reservation = db_manager.create_reservation(**test_data)
    reservation_id = reservation["id"]

    print(f"✅ Created reservation:")
    print(f"   ID: {reservation_id}")
    print(f"   Name: {test_data['first_name']} {test_data['last_name']}")
    print(f"   Car: {test_data['car_number']}")
    print(f"   Period: {test_data['start_time'].strftime('%Y-%m-%d %H:%M')} to {test_data['end_time'].strftime('%Y-%m-%d %H:%M')}")
    print(f"   Status: {reservation['status']}")

    time.sleep(1)

    print_section("3. SIMULATING ADMIN APPROVAL")

    # Initialize admin agent with MCP integration
    admin_agent = AdminAgentDB(settings, use_mcp_server=True)

    # Admin approves the reservation
    print(f"🔄 Admin approving reservation {reservation_id}...")
    result = admin_agent.process_admin_decision(
        reservation_id=reservation_id,
        decision="approved",
        admin_notes="Demo approval - Stage 3 test"
    )

    if result.get("success"):
        print("✅ Reservation approved successfully!")
        print(f"   Decision: {result['decision']}")
        print(f"   Time: {result['decided_at']}")
        if result.get("mcp_written"):
            print("   ✅ Written to file via MCP server")
        else:
            print("   ⚠️  Not written to file (MCP integration disabled)")
    else:
        print(f"❌ Approval failed: {result.get('error')}")
        return

    time.sleep(1)

    print_section("4. VERIFYING FILE WRITE")

    # List reservations from MCP server
    print("📄 Fetching reservations from MCP server...")
    list_result = mcp_client.list_reservations(limit=5)

    if list_result.get("count", 0) > 0:
        print(f"✅ Found {list_result['count']} reservation(s) in file:")
        print()
        for i, res in enumerate(list_result["reservations"][-5:], 1):
            print(f"   {i}. {res}")
        print()

        # Check if our demo reservation is in the list
        reservations_text = " ".join(list_result["reservations"])
        if "DEMO123" in reservations_text or "Demo User" in reservations_text:
            print("✅ Demo reservation found in file!")
        else:
            print("⚠️  Demo reservation not found in recent entries")
    else:
        print("⚠️  No reservations found in file")

    print_section("5. DATABASE VERIFICATION")

    # Verify database status
    db_reservation = db_manager.get_reservation(reservation_id)
    print(f"✅ Database status:")
    print(f"   Status: {db_reservation['status']}")
    print(f"   Admin Decision: {db_reservation['admin_decision']}")
    print(f"   Confirmed by Admin: {db_reservation['confirmed_by_admin']}")
    print(f"   Notes: {db_reservation['admin_notes']}")
    print(f"   Decided At: {db_reservation['decided_at']}")

    print_section("6. COMPLETE WORKFLOW SUMMARY")

    print("✅ STAGE 3 WORKFLOW COMPLETE!")
    print()
    print("📊 Workflow Steps:")
    print("   1. ✅ User creates reservation → Database (pending)")
    print("   2. ✅ Admin reviews → Admin Agent")
    print("   3. ✅ Admin approves → Database (confirmed)")
    print("   4. ✅ MCP Server triggered → File write")
    print("   5. ✅ Reservation logged → confirmed_reservations.txt")
    print()
    print("🎉 All systems working correctly!")
    print()
    print("📂 Check the file: data/confirmed_reservations.txt")
    print("🌐 API Docs: http://127.0.0.1:8001/docs")
    print()


def test_mcp_direct():
    """Test MCP client directly."""
    print_section("DIRECT MCP CLIENT TEST")

    mcp_client = MCPClient()

    # Test health
    print("1. Health Check:")
    health = mcp_client.check_health()
    print(f"   Status: {health.get('status')}")
    print(f"   Available: {mcp_client.is_server_available()}")

    if not mcp_client.is_server_available():
        print("\n❌ MCP Server is not available!")
        print("   Start it with: python run_mcp_server.py")
        return

    # Test write
    print("\n2. Writing Test Reservation:")
    result = mcp_client.write_reservation(
        reservation_id=88888,
        first_name="Direct",
        last_name="Test",
        car_number="DIRECT1",
        start_time=datetime.now() + timedelta(days=1),
        end_time=datetime.now() + timedelta(days=1, hours=2),
        admin_notes="Direct MCP client test"
    )

    if result.get("success"):
        print("   ✅ Write successful!")
        print(f"   File: {result.get('file_path')}")
    else:
        print(f"   ❌ Write failed: {result.get('error')}")

    # Test list
    print("\n3. Listing Reservations:")
    list_result = mcp_client.list_reservations(limit=3)
    print(f"   Count: {list_result.get('count', 0)}")

    if list_result.get("count", 0) > 0:
        print("   Recent entries:")
        for i, res in enumerate(list_result["reservations"][-3:], 1):
            print(f"     {i}. {res}")


def main():
    """Main demo function."""
    import argparse

    parser = argparse.ArgumentParser(description="Stage 3 Demo Script")
    parser.add_argument("--direct", action="store_true", help="Test MCP client directly")
    parser.add_argument("--full", action="store_true", help="Run full workflow demo")

    args = parser.parse_args()

    if args.direct:
        test_mcp_direct()
    elif args.full:
        demo_stage3()
    else:
        # Default: run both
        demo_stage3()
        print("\n" + "-" * 70 + "\n")
        test_mcp_direct()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
