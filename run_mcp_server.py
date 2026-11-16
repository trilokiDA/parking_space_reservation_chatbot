"""
Script to run the MCP server.
Stage 3: Reservation file writing service.
"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import and run the MCP server
if __name__ == "__main__":
    from src.mcp_server.mcp_server import app, ensure_data_directory, SERVER_API_KEY, RESERVATIONS_FILE
    import uvicorn

    # Ensure data directory exists
    ensure_data_directory()

    # Print server information
    print("\n" + "=" * 70)
    print("🚀 MCP SERVER - STAGE 3")
    print("=" * 70)
    print(f"📝 Data File: {RESERVATIONS_FILE.absolute()}")
    print(f"🔑 API Key: {SERVER_API_KEY}")
    print(f"🌐 Server URL: http://127.0.0.1:8001")
    print(f"💚 Health Check: http://127.0.0.1:8001/health")
    print("\n⚠️  IMPORTANT: Keep this terminal open while using the system")
    print("=" * 70 + "\n")

    # Run server
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8001,
        log_level="info"
    )
