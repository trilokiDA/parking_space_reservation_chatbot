"""Test approving reservation 16 directly."""
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))
load_dotenv()

from src.config.settings import get_settings
from src.admin_agent.admin_agent_db import AdminAgentDB
from src.database.db_manager import DatabaseManager

print("=" * 70)
print("DIRECT TEST - RESERVATION 16")
print("=" * 70)

settings = get_settings()
db_manager = DatabaseManager(settings.database_url)

# Check current status
print("\n1. Current Status:")
res = db_manager.get_reservation(16)
if res:
    print(f"   ID: {res['id']}")
    print(f"   Name: {res['first_name']} {res['last_name']}")
    print(f"   Car: {res['car_number']}")
    print(f"   Status: {res['status']}")
    print(f"   Admin Decision: {res['admin_decision']}")
else:
    print("   ✗ Reservation 16 not found!")
    sys.exit(1)

# Initialize admin agent
print("\n2. Initializing Admin Agent:")
admin_agent = AdminAgentDB(settings, use_mcp_server=True)
print(f"   use_mcp_server: {admin_agent.use_mcp_server}")
print(f"   mcp_client exists: {admin_agent.mcp_client is not None}")

if admin_agent.mcp_client:
    print(f"   mcp_client.api_key: {admin_agent.mcp_client.api_key[:20]}...")
    print(f"   mcp_client.base_url: {admin_agent.mcp_client.base_url}")

# Approve
print("\n3. Approving reservation 16:")
result = admin_agent.process_admin_decision(
    reservation_id=16,
    decision="approved",
    admin_notes="Direct test approval"
)

print(f"   Success: {result.get('success')}")
print(f"   Decision: {result.get('decision')}")
print(f"   MCP Written: {result.get('mcp_written')}")

if not result.get('success'):
    print(f"   Error: {result.get('error')}")

# Check file
print("\n4. Checking confirmed_reservations.txt:")
try:
    with open("data/confirmed_reservations.txt", "r") as f:
        content = f.read()
        if "reservation 16" in content.lower() or res['car_number'] in content:
            print(f"   ✓ Found reservation in file!")
            # Print the line
            for line in content.split('\n'):
                if res['car_number'] in line:
                    print(f"   {line}")
        else:
            print(f"   ✗ Reservation NOT in file")
            print(f"\n   Last 2 lines:")
            lines = [l for l in content.split('\n') if l.strip() and not l.startswith('#')]
            for line in lines[-2:]:
                print(f"   {line}")
except Exception as e:
    print(f"   Error: {e}")

print("\n" + "=" * 70)
