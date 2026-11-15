"""Simplified Admin Agent for handling reservation approval requests."""
import logging
import re
from typing import Dict, Any, Optional
from datetime import datetime
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)


class AdminAgent:
    """Simplified agent for administrator interactions."""

    def __init__(self, settings):
        """Initialize the admin agent.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.llm = self._initialize_llm()
        self.pending_requests = {}  # In-memory storage for demo (reservation_id -> request_data)

    def _initialize_llm(self):
        """Initialize the language model."""
        try:
            # Try Groq first if configured
            if hasattr(self.settings, 'groq_api_key') and self.settings.groq_api_key:
                try:
                    from langchain_groq import ChatGroq
                    logger.info("Using Groq for admin agent")
                    return ChatGroq(
                        model=self.settings.llm_model,
                        temperature=0.3,  # Lower temperature for admin decisions
                        groq_api_key=self.settings.groq_api_key
                    )
                except Exception as e:
                    logger.warning(f"Groq initialization failed, falling back to OpenAI: {e}")

            # Fallback to OpenAI
            logger.info("Using OpenAI for admin agent")
            return ChatOpenAI(
                model=self.settings.llm_model,
                temperature=0.3,
                openai_api_key=self.settings.openai_api_key
            )
        except Exception as e:
            logger.error(f"Error initializing LLM: {e}")
            raise

    def add_pending_request(self, reservation_id: int, request_data: Dict[str, Any]) -> bool:
        """Add a new pending reservation request.

        Args:
            reservation_id: Unique reservation ID
            request_data: Reservation details

        Returns:
            True if added successfully
        """
        try:
            self.pending_requests[reservation_id] = {
                **request_data,
                "requested_at": datetime.now().isoformat(),
                "status": "pending"
            }
            logger.info(f"Added pending request for reservation {reservation_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding pending request: {e}")
            return False

    def get_pending_requests(self) -> str:
        """Get all pending reservation requests.

        Returns:
            Formatted string with pending requests
        """
        if not self.pending_requests:
            return "No pending reservation requests at this time."

        result = "📋 **Pending Reservation Requests**\n\n"
        for res_id, request in self.pending_requests.items():
            if request.get("status") == "pending":
                result += f"**Reservation ID: {res_id}**\n"
                result += f"  Name: {request.get('first_name')} {request.get('last_name')}\n"
                result += f"  Car Number: {request.get('car_number')}\n"
                result += f"  Start: {request.get('start_time')}\n"
                result += f"  End: {request.get('end_time')}\n"
                result += f"  Requested: {request.get('requested_at')}\n"
                result += "-" * 50 + "\n"

        return result

    def get_request_details(self, reservation_id: int) -> str:
        """Get detailed information about a specific reservation request.

        Args:
            reservation_id: The reservation ID

        Returns:
            Formatted string with request details
        """
        if reservation_id not in self.pending_requests:
            return f"No request found with ID {reservation_id}"

        request = self.pending_requests[reservation_id]

        details = f"""
**Reservation Request Details**

Reservation ID: {reservation_id}
Status: {request.get('status', 'unknown')}

**User Information:**
- Name: {request.get('first_name')} {request.get('last_name')}
- Car Registration: {request.get('car_number')}

**Reservation Period:**
- Start Time: {request.get('start_time')}
- End Time: {request.get('end_time')}

**Request Metadata:**
- Requested At: {request.get('requested_at')}
- Parking Space: {request.get('parking_space', 'Not assigned yet')}

**Admin Decision:** {request.get('admin_decision', 'Pending')}
"""
        return details

    def process_admin_decision(
        self,
        reservation_id: int,
        decision: str,
        admin_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process admin decision on a reservation request.

        Args:
            reservation_id: Reservation ID
            decision: 'approved' or 'rejected'
            admin_notes: Optional notes from admin

        Returns:
            Result dictionary with decision details
        """
        if reservation_id not in self.pending_requests:
            return {
                "success": False,
                "error": f"Reservation {reservation_id} not found"
            }

        if decision not in ['approved', 'rejected']:
            return {
                "success": False,
                "error": "Decision must be 'approved' or 'rejected'"
            }

        try:
            self.pending_requests[reservation_id].update({
                "status": decision,
                "admin_decision": decision,
                "admin_notes": admin_notes,
                "decided_at": datetime.now().isoformat()
            })

            logger.info(f"Reservation {reservation_id} {decision} by admin")

            return {
                "success": True,
                "reservation_id": reservation_id,
                "decision": decision,
                "admin_notes": admin_notes,
                "decided_at": self.pending_requests[reservation_id]["decided_at"]
            }
        except Exception as e:
            logger.error(f"Error processing admin decision: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def query_admin(self, query: str) -> str:
        """Process admin query using the LLM.

        Args:
            query: Admin's question or request

        Returns:
            Agent's response
        """
        try:
            # Get context based on the query
            context = ""
            if "pending" in query.lower():
                context = self.get_pending_requests()
            elif "detail" in query.lower() and any(char.isdigit() for char in query):
                # Extract reservation ID from query
                ids = re.findall(r'\d+', query)
                if ids:
                    context = self.get_request_details(int(ids[0]))

            # Create system prompt
            system_prompt = """You are an intelligent admin assistant for a parking reservation system.

Your role is to:
1. Review reservation requests from users
2. Provide clear summaries of pending requests
3. Help admins make informed decisions about approving or rejecting reservations
4. Explain the details of each request when asked

When presenting reservation information:
- Use clear, structured format
- Highlight important details (dates, times, user info)
- Note any potential conflicts or concerns
- Be professional and concise

Always format dates and times in a readable way."""

            # Create messages for the LLM
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context:\n{context}\n\nQuery: {query}"}
            ]

            # Call LLM
            if hasattr(self.llm, 'invoke'):
                response = self.llm.invoke(messages)
                if hasattr(response, 'content'):
                    return response.content
                return str(response)
            else:
                # Fallback
                return context if context else "Please use specific commands like 'pending' or 'details <id>'"

        except Exception as e:
            logger.error(f"Error processing admin query: {e}")
            return f"Error processing query: {str(e)}"

    def get_reservation_status(self, reservation_id: int) -> Optional[Dict[str, Any]]:
        """Get the current status of a reservation request.

        Args:
            reservation_id: Reservation ID

        Returns:
            Reservation status information
        """
        if reservation_id not in self.pending_requests:
            return None

        request = self.pending_requests[reservation_id]
        return {
            "reservation_id": reservation_id,
            "status": request.get("status"),
            "admin_decision": request.get("admin_decision"),
            "admin_notes": request.get("admin_notes"),
            "decided_at": request.get("decided_at")
        }
