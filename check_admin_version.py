"""Check if admin_agent_db.py has the MCP fix."""
import inspect
from src.admin_agent.admin_agent_db import AdminAgentDB

# Get the source code of process_admin_decision
source = inspect.getsource(AdminAgentDB.process_admin_decision)

print("=" * 70)
print("CHECKING ADMIN AGENT CODE VERSION")
print("=" * 70)

# Check for the fix
has_date_parser = "date_parser" in source
has_isinstance_check = "isinstance(start_time, str)" in source
has_mcp_logging = "[MCP]" in source

print(f"\n✓ Has date_parser import: {has_date_parser}")
print(f"✓ Has isinstance check: {has_isinstance_check}")
print(f"✓ Has MCP logging: {has_mcp_logging}")

if has_date_parser and has_isinstance_check:
    print("\n✅ CODE HAS THE FIX")
else:
    print("\n❌ CODE DOES NOT HAVE THE FIX")
    print("   You need to restart Terminal 2!")

print("\n" + "=" * 70)
