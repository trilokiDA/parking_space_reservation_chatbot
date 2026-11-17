"""Test approval process for reservation 13."""
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))
load_dotenv()

from src.config.settings import get_settings
from src.admin_agent.admin_agent_db import AdminAgentDB
from src.database.db_manager import DatabaseManager

print("=" * 70)
print("TESTING APPROVAL PROCESS")
print("=" * 70)

settings = get_settings()
db_manager = DatabaseManager(settings.database_url)

# Check reservation before approval
print("\n1. BEFORE APPROVAL:")
res_before = db_manager.get_reservation(13)
print(f"   Status: {res_before['status']}")
print(f"   Admin Decision: {res_before['admin_decision']}")

# Initialize admin agent with MCP
print("\n2. INITIALIZING ADMIN AGENT:")
admin_agent = AdminAgentDB(settings, use_mcp_server=True)
print(f"   use_mcp_server: {admin_agent.use_mcp_server}")
print(f"   mcp_client exists: {admin_agent.mcp_client is not None}")

# Process approval
print("\n3. PROCESSING APPROVAL:")
result = admin_agent.process_admin_decision(
    reservation_id=13,
    decision="approved",
    admin_notes="Test approval from script"
)

print(f"   Success: {result.get('success')}")
if result.get('success'):
    print(f"   Decision: {result.get('decision')}")
    print(f"   MCP Written: {result.get('mcp_written')}")
    print(f"   Decided At: {result.get('decided_at')}")
else:
    print(f"   Error: {result.get('error')}")

# Check reservation after approval
print("\n4. AFTER APPROVAL:")
res_after = db_manager.get_reservation(13)
print(f"   Status: {res_after['status']}")
print(f"   Admin Decision: {res_after['admin_decision']}")
print(f"   Admin Notes: {res_after['admin_notes']}")
print(f"   Decided At: {res_after['decided_at']}")

# Check file
print("\n5. CHECKING FILE:")
try:
    with open("data/confirmed_reservations.txt", "r") as f:
        lines = f.readlines()
        print(f"   Total lines: {len(lines)}")
        found = False
        for line in lines:
            if "Triloki Gupta" in line or "ABCDEF1234" in line:
                print(f"   ✓ FOUND: {line.strip()}")
                found = True
        if not found:
            print("   ✗ NOT FOUND in file")
            print("\n   Last 3 entries:")
            for line in lines[-3:]:
                if line.strip() and not line.startswith('#'):
                    print(f"     {line.strip()}")
except Exception as e:
    print(f"   ERROR: {e}")

print("\n" + "=" * 70)
