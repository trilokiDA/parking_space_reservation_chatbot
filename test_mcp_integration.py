"""
Test script to debug MCP integration.
"""
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment
load_dotenv()

print("=" * 70)
print("MCP INTEGRATION DEBUG TEST")
print("=" * 70)

# Step 1: Check environment
print("\n1. Environment Check:")
mcp_key = os.getenv("MCP_SERVER_API_KEY")
print(f"   MCP_SERVER_API_KEY set: {'✓' if mcp_key else '✗'}")
if mcp_key:
    print(f"   API Key (first 10 chars): {mcp_key[:10]}...")

# Step 2: Test MCP Client directly
print("\n2. Testing MCP Client directly:")
from src.mcp_server.mcp_client import MCPClient

mcp_client = MCPClient()
print(f"   Client initialized: ✓")
print(f"   Base URL: {mcp_client.base_url}")
print(f"   API Key set: {'✓' if mcp_client.api_key else '✗'}")

# Check health
health = mcp_client.check_health()
print(f"   Server health: {health.get('status')}")

if health.get('status') != 'healthy':
    print(f"   ERROR: {health.get('error')}")
    print("\n❌ MCP Server is not running! Please start it first:")
    print("   python run_mcp_server.py")
    sys.exit(1)

# Step 3: Test writing a reservation
print("\n3. Testing write_reservation:")
test_result = mcp_client.write_reservation(
    reservation_id=99999,
    first_name="Test",
    last_name="Debug",
    car_number="TEST999",
    start_time=datetime.now() + timedelta(days=1),
    end_time=datetime.now() + timedelta(days=1, hours=2),
    admin_notes="Debug test from test script"
)

print(f"   Success: {test_result.get('success')}")
if test_result.get('success'):
    print(f"   File path: {test_result.get('file_path')}")
    print("   ✓ Write successful!")
else:
    print(f"   ERROR: {test_result.get('error')}")

# Step 4: Read the file
print("\n4. Reading confirmed_reservations.txt:")
try:
    with open("data/confirmed_reservations.txt", "r") as f:
        lines = f.readlines()
        print(f"   Total lines: {len(lines)}")
        print(f"   Last 3 entries:")
        for line in lines[-3:]:
            if line.strip() and not line.startswith('#'):
                print(f"     {line.strip()}")
except Exception as e:
    print(f"   ERROR reading file: {e}")

# Step 5: Test AdminAgentDB
print("\n5. Testing AdminAgentDB with MCP integration:")
from src.config.settings import get_settings
from src.admin_agent.admin_agent_db import AdminAgentDB

settings = get_settings()
admin_agent = AdminAgentDB(settings, use_mcp_server=True)

print(f"   use_mcp_server: {admin_agent.use_mcp_server}")
print(f"   mcp_client exists: {'✓' if admin_agent.mcp_client else '✗'}")

if admin_agent.mcp_client:
    print(f"   mcp_client.api_key set: {'✓' if admin_agent.mcp_client.api_key else '✗'}")
else:
    print("   ⚠️  WARNING: mcp_client is None!")

print("\n" + "=" * 70)
print("DEBUG TEST COMPLETE")
print("=" * 70)
