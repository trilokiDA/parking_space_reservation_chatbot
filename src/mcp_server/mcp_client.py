"""
MCP Client for communicating with the MCP server.
Handles reservation data submission to the file writing service.
"""
import requests
import logging
from datetime import datetime
from typing import Dict, Optional
import os

logger = logging.getLogger(__name__)


class MCPClient:
    """Client for interacting with the MCP reservation server."""

    def __init__(self, base_url: str = "http://127.0.0.1:8001", api_key: Optional[str] = None):
        """
        Initialize MCP client.

        Args:
            base_url: Base URL of the MCP server
            api_key: API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key or os.getenv("MCP_SERVER_API_KEY", "")
        self.session = requests.Session()

        if self.api_key:
            self.session.headers.update({
                "X-API-Key": self.api_key,
                "Content-Type": "application/json"
            })

    def check_health(self) -> Dict:
        """
        Check if MCP server is running.

        Returns:
            Health check response
        """
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    def write_reservation(
        self,
        reservation_id: int,
        first_name: str,
        last_name: str,
        car_number: str,
        start_time: datetime,
        end_time: datetime,
        approval_time: Optional[datetime] = None,
        admin_notes: Optional[str] = None
    ) -> Dict:
        """
        Write a confirmed reservation to the MCP server.

        Args:
            reservation_id: Unique reservation ID
            first_name: Customer's first name
            last_name: Customer's last name
            car_number: Vehicle registration number
            start_time: Reservation start time
            end_time: Reservation end time
            approval_time: Time of admin approval
            admin_notes: Optional admin notes

        Returns:
            Response from MCP server
        """
        try:
            data = {
                "reservation_id": reservation_id,
                "first_name": first_name,
                "last_name": last_name,
                "car_number": car_number,
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "approval_time": (approval_time or datetime.now()).isoformat(),
                "admin_notes": admin_notes
            }

            logger.info(f"Sending reservation {reservation_id} to MCP server")

            response = self.session.post(
                f"{self.base_url}/api/v1/reservations/write",
                json=data,
                timeout=10
            )

            response.raise_for_status()
            result = response.json()

            logger.info(f"Successfully sent reservation {reservation_id} to MCP server")
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to write reservation to MCP server: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to communicate with MCP server"
            }

    def list_reservations(self, limit: int = 100) -> Dict:
        """
        List recent reservations from MCP server.

        Args:
            limit: Maximum number of reservations to retrieve

        Returns:
            List of reservations
        """
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/reservations/list",
                params={"limit": limit},
                timeout=10
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to list reservations: {e}")
            return {
                "count": 0,
                "reservations": [],
                "error": str(e)
            }

    def is_server_available(self) -> bool:
        """
        Check if MCP server is available.

        Returns:
            True if server is healthy, False otherwise
        """
        health = self.check_health()
        return health.get("status") == "healthy"


# Singleton instance
_mcp_client_instance: Optional[MCPClient] = None


def get_mcp_client(base_url: str = "http://127.0.0.1:8001", api_key: Optional[str] = None) -> MCPClient:
    """
    Get or create MCP client singleton instance.

    Args:
        base_url: Base URL of MCP server
        api_key: API key for authentication

    Returns:
        MCPClient instance
    """
    global _mcp_client_instance

    if _mcp_client_instance is None:
        _mcp_client_instance = MCPClient(base_url=base_url, api_key=api_key)

    return _mcp_client_instance
