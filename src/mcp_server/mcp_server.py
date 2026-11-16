"""
MCP Server for processing confirmed reservations.
Stage 3 Implementation - Secure file-based reservation storage.
"""
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime
from pathlib import Path
import logging
import secrets
import os
from typing import Optional
import threading
import platform

# Import file locking for Unix/Linux systems
if platform.system() != 'Windows':
    try:
        import fcntl
        HAS_FCNTL = True
    except ImportError:
        HAS_FCNTL = False
else:
    HAS_FCNTL = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Reservation MCP Server",
    description="Secure MCP server for processing confirmed parking reservations",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
RESERVATIONS_FILE = Path("data/confirmed_reservations.txt")
API_KEY_ENV = "MCP_SERVER_API_KEY"
file_lock = threading.Lock()

# Generate or load API key
def get_api_key() -> str:
    """Get or generate API key for server authentication."""
    api_key = os.getenv(API_KEY_ENV)
    if not api_key:
        # Generate a secure random API key
        api_key = secrets.token_urlsafe(32)
        logger.warning(f"No API key found in environment. Generated temporary key: {api_key}")
        logger.warning(f"Set {API_KEY_ENV} environment variable for production use.")
    return api_key

SERVER_API_KEY = get_api_key()


class ReservationData(BaseModel):
    """Model for reservation data."""
    reservation_id: int = Field(..., description="Unique reservation ID")
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    car_number: str = Field(..., min_length=1, max_length=15)
    start_time: datetime
    end_time: datetime
    approval_time: Optional[datetime] = None
    admin_notes: Optional[str] = None


class WriteResponse(BaseModel):
    """Response model for write operations."""
    success: bool
    message: str
    reservation_id: int
    file_path: str


def verify_api_key(x_api_key: str = Header(...)) -> str:
    """Verify API key from request header."""
    if x_api_key != SERVER_API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    return x_api_key


def ensure_data_directory():
    """Ensure data directory exists."""
    RESERVATIONS_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Create file with header if it doesn't exist
    if not RESERVATIONS_FILE.exists():
        with open(RESERVATIONS_FILE, 'w', encoding='utf-8') as f:
            f.write("# Confirmed Parking Reservations\n")
            f.write("# Format: Name | Car Number | Reservation Period | Approval Time\n")
            f.write("# " + "=" * 70 + "\n")
            f.flush()


def format_reservation_entry(data: ReservationData) -> str:
    """
    Format reservation data for file storage.

    Format: Name | Car Number | Reservation Period | Approval Time
    Example: John Doe | ABC123 | 2024-12-25 14:00 to 2024-12-25 18:00 | 2024-12-24 10:30:15
    """
    full_name = f"{data.first_name} {data.last_name}"
    reservation_period = f"{data.start_time.strftime('%Y-%m-%d %H:%M')} to {data.end_time.strftime('%Y-%m-%d %H:%M')}"
    approval_time = (data.approval_time or datetime.now()).strftime('%Y-%m-%d %H:%M:%S')

    entry = f"{full_name} | {data.car_number} | {reservation_period} | {approval_time}"

    if data.admin_notes:
        entry += f" | Notes: {data.admin_notes}"

    return entry


def write_reservation_to_file(data: ReservationData) -> bool:
    """
    Write reservation to file with proper locking for thread safety.

    Args:
        data: ReservationData object

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Use thread lock for file access
        with file_lock:
            ensure_data_directory()

            entry = format_reservation_entry(data)

            # Write to file with proper encoding and flushing
            with open(RESERVATIONS_FILE, 'a', encoding='utf-8') as f:
                # For Unix systems, use file locking
                if HAS_FCNTL:
                    try:
                        import fcntl
                        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                    except Exception:
                        pass  # Fallback to thread lock only

                f.write(f"{entry}\n")
                f.flush()
                os.fsync(f.fileno())  # Ensure data is written to disk

                if HAS_FCNTL:
                    try:
                        import fcntl
                        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                    except Exception:
                        pass

            logger.info(f"Successfully wrote reservation {data.reservation_id} to file")
            return True

    except Exception as e:
        logger.error(f"Error writing reservation to file: {e}")
        return False


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Reservation MCP Server",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "file_exists": RESERVATIONS_FILE.exists(),
        "file_path": str(RESERVATIONS_FILE.absolute())
    }


@app.post("/api/v1/reservations/write", response_model=WriteResponse)
async def write_reservation(
    data: ReservationData,
    api_key: str = Depends(verify_api_key)
):
    """
    Write a confirmed reservation to file.

    Requires API key authentication via X-API-Key header.

    Args:
        data: ReservationData containing reservation details
        api_key: API key for authentication (from header)

    Returns:
        WriteResponse with success status and details
    """
    try:
        logger.info(f"Received write request for reservation {data.reservation_id}")

        # Validate data
        if data.end_time <= data.start_time:
            raise HTTPException(
                status_code=400,
                detail="End time must be after start time"
            )

        # Set approval time if not provided
        if not data.approval_time:
            data.approval_time = datetime.now()

        # Write to file
        success = write_reservation_to_file(data)

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to write reservation to file"
            )

        return WriteResponse(
            success=True,
            message="Reservation successfully written to file",
            reservation_id=data.reservation_id,
            file_path=str(RESERVATIONS_FILE.absolute())
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing write request: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/api/v1/reservations/list")
async def list_reservations(
    api_key: str = Depends(verify_api_key),
    limit: int = 100
):
    """
    List recent reservations from file.

    Args:
        api_key: API key for authentication
        limit: Maximum number of reservations to return

    Returns:
        List of reservation entries
    """
    try:
        if not RESERVATIONS_FILE.exists():
            return {
                "count": 0,
                "reservations": []
            }

        with open(RESERVATIONS_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Filter out comments and empty lines
        reservations = [
            line.strip()
            for line in lines
            if line.strip() and not line.startswith('#')
        ]

        # Return most recent entries
        recent = reservations[-limit:] if len(reservations) > limit else reservations

        return {
            "count": len(recent),
            "total_count": len(reservations),
            "reservations": recent
        }

    except Exception as e:
        logger.error(f"Error listing reservations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error reading reservations: {str(e)}"
        )


@app.delete("/api/v1/reservations/clear")
async def clear_reservations(
    api_key: str = Depends(verify_api_key),
    confirm: bool = False
):
    """
    Clear all reservations from file (admin only).

    Args:
        api_key: API key for authentication
        confirm: Must be True to execute

    Returns:
        Success message
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Must set confirm=true to clear reservations"
        )

    try:
        if RESERVATIONS_FILE.exists():
            # Backup existing file
            backup_path = RESERVATIONS_FILE.with_suffix('.txt.backup')
            RESERVATIONS_FILE.rename(backup_path)
            logger.info(f"Backed up existing file to {backup_path}")

        # Recreate file with header
        ensure_data_directory()

        return {
            "success": True,
            "message": "Reservations file cleared successfully",
            "backup_created": str(backup_path) if backup_path.exists() else None
        }

    except Exception as e:
        logger.error(f"Error clearing reservations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error clearing file: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    # Ensure data directory exists
    ensure_data_directory()

    # Print API key info
    print("\n" + "=" * 70)
    print("MCP SERVER STARTING")
    print("=" * 70)
    print(f"API Key: {SERVER_API_KEY}")
    print(f"Data File: {RESERVATIONS_FILE.absolute()}")
    print("=" * 70 + "\n")

    # Run server
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8001,
        log_level="info"
    )
