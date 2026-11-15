"""Communication service for chatbot-admin interaction."""
import logging
import requests
from typing import Dict, Any, Optional
from time import sleep

logger = logging.getLogger(__name__)


class CommunicationService:
    """Service for communicating with the admin API."""

    def __init__(self, api_url: str = "http://127.0.0.1:5000"):
        """Initialize communication service.

        Args:
            api_url: Base URL of the admin API
        """
        self.api_url = api_url.rstrip('/')
        self.timeout = 10  # Request timeout in seconds

    def send_reservation_to_admin(
        self,
        reservation_id: int,
        reservation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send a reservation request to admin for approval.

        Args:
            reservation_id: Unique reservation ID
            reservation_data: Reservation details

        Returns:
            Response dictionary
        """
        try:
            data = {
                "reservation_id": reservation_id,
                **reservation_data
            }

            response = requests.post(
                f"{self.api_url}/api/reservations/submit",
                json=data,
                timeout=self.timeout
            )

            if response.status_code in [200, 201]:
                logger.info(f"Reservation {reservation_id} sent to admin successfully")
                return {
                    "success": True,
                    "message": "Reservation sent to admin for approval",
                    "data": response.json()
                }
            else:
                logger.error(f"Failed to send reservation: {response.status_code}")
                return {
                    "success": False,
                    "error": response.json().get('error', 'Unknown error')
                }

        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to admin API server")
            return {
                "success": False,
                "error": "Admin service is currently unavailable"
            }
        except Exception as e:
            logger.error(f"Error sending reservation to admin: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def check_reservation_status(self, reservation_id: int) -> Optional[Dict[str, Any]]:
        """Check the status of a reservation request.

        Args:
            reservation_id: Reservation ID to check

        Returns:
            Status information or None if not found
        """
        try:
            response = requests.get(
                f"{self.api_url}/api/reservations/{reservation_id}/status",
                timeout=self.timeout
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return result.get('status')

            return None

        except Exception as e:
            logger.error(f"Error checking reservation status: {e}")
            return None

    def wait_for_admin_decision(
        self,
        reservation_id: int,
        max_wait_seconds: int = 300,
        poll_interval: int = 5
    ) -> Optional[str]:
        """Wait for admin decision on a reservation (polling).

        Args:
            reservation_id: Reservation ID
            max_wait_seconds: Maximum time to wait
            poll_interval: Seconds between status checks

        Returns:
            Decision ('approved' or 'rejected') or None if timeout
        """
        elapsed = 0

        while elapsed < max_wait_seconds:
            status = self.check_reservation_status(reservation_id)

            if status and status.get('status') in ['approved', 'rejected']:
                logger.info(f"Admin decision received for {reservation_id}: {status.get('status')}")
                return status.get('status')

            sleep(poll_interval)
            elapsed += poll_interval

        logger.warning(f"Timeout waiting for admin decision on {reservation_id}")
        return None

    def get_pending_reservations(self) -> Optional[Dict[str, Any]]:
        """Get all pending reservation requests.

        Returns:
            Pending reservations data
        """
        try:
            response = requests.get(
                f"{self.api_url}/api/reservations/pending",
                timeout=self.timeout
            )

            if response.status_code == 200:
                return response.json()

            return None

        except Exception as e:
            logger.error(f"Error getting pending reservations: {e}")
            return None

    def health_check(self) -> bool:
        """Check if admin API is healthy.

        Returns:
            True if healthy, False otherwise
        """
        try:
            response = requests.get(
                f"{self.api_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False

    def simulate_admin_decision(
        self,
        reservation_id: int,
        decision: str,
        notes: str = ""
    ) -> Dict[str, Any]:
        """Simulate admin decision (for testing/demo purposes).

        Args:
            reservation_id: Reservation ID
            decision: 'approved' or 'rejected'
            notes: Optional admin notes

        Returns:
            Response dictionary
        """
        try:
            data = {
                "decision": decision,
                "notes": notes
            }

            response = requests.post(
                f"{self.api_url}/api/reservations/{reservation_id}/decide",
                json=data,
                timeout=self.timeout
            )

            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": response.json().get('error', 'Unknown error')
                }

        except Exception as e:
            logger.error(f"Error simulating admin decision: {e}")
            return {
                "success": False,
                "error": str(e)
            }
