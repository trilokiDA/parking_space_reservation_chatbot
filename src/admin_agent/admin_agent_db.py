"""Database-backed Admin Agent for handling reservation approval requests."""
import logging
import re
from typing import Dict, Any, Optional
from datetime import datetime
from langchain_openai import ChatOpenAI
from ..database.db_manager import DatabaseManager
from ..mcp_server.mcp_client import get_mcp_client

logger = logging.getLogger(__name__)


class AdminAgentDB:
    """Admin agent that uses database instead of in-memory storage."""

    def __init__(self, settings, use_mcp_server: bool = True):
        """Initialize the admin agent with database support.

        Args:
            settings: Application settings
            use_mcp_server: Whether to use MCP server for file writing (Stage 3)
        """
        self.settings = settings
        self.llm = self._initialize_llm()
        self.db_manager = DatabaseManager(settings.database_url)
        self.use_mcp_server = use_mcp_server

        # Initialize MCP client if enabled
        if self.use_mcp_server:
            try:
                self.mcp_client = get_mcp_client()
                logger.info("MCP client initialized for Stage 3 integration")
            except Exception as e:
                logger.warning(f"Failed to initialize MCP client: {e}")
                self.mcp_client = None
        else:
            self.mcp_client = None

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

        Note: This is a no-op since reservations are already in the database.
        Kept for API compatibility.

        Args:
            reservation_id: Unique reservation ID
            request_data: Reservation details

        Returns:
            True if reservation exists in database
        """
        try:
            reservation = self.db_manager.get_reservation(reservation_id)
            if reservation:
                logger.info(f"Reservation {reservation_id} found in database")
                return True
            else:
                logger.warning(f"Reservation {reservation_id} not found in database")
                return False
        except Exception as e:
            logger.error(f"Error checking reservation: {e}")
            return False

    def get_pending_requests(self) -> str:
        """Get all pending reservation requests from database.

        Returns:
            Formatted string with pending requests
        """
        try:
            reservations = self.db_manager.get_all_reservations(status="pending")

            if not reservations:
                return "No pending reservation requests at this time."

            result = "📋 **Pending Reservation Requests**\n\n"
            for res in reservations:
                result += f"**Reservation ID: {res['id']}**\n"
                result += f"  Name: {res['first_name']} {res['last_name']}\n"
                result += f"  Car Number: {res['car_number']}\n"
                result += f"  Start: {res['start_time']}\n"
                result += f"  End: {res['end_time']}\n"
                result += f"  Created: {res['created_at']}\n"
                result += "-" * 50 + "\n"

            return result
        except Exception as e:
            logger.error(f"Error getting pending requests: {e}")
            return f"Error retrieving pending requests: {str(e)}"

    def get_request_details(self, reservation_id: int) -> str:
        """Get detailed information about a specific reservation request from database.

        Args:
            reservation_id: The reservation ID

        Returns:
            Formatted string with request details
        """
        try:
            reservation = self.db_manager.get_reservation(reservation_id)

            if not reservation:
                return f"No request found with ID {reservation_id}"

            details = f"""
**Reservation Request Details**

Reservation ID: {reservation_id}
Status: {reservation.get('status', 'unknown')}

**User Information:**
- Name: {reservation.get('first_name')} {reservation.get('last_name')}
- Car Registration: {reservation.get('car_number')}

**Reservation Period:**
- Start Time: {reservation.get('start_time')}
- End Time: {reservation.get('end_time')}

**Request Metadata:**
- Created At: {reservation.get('created_at', 'N/A')}
- Parking Space: {reservation.get('parking_space', 'Not assigned yet')}

**Admin Decision:** {reservation.get('admin_decision', 'Pending')}
"""
            if reservation.get('admin_notes'):
                details += f"**Admin Notes:** {reservation['admin_notes']}\n"
            if reservation.get('decided_at'):
                details += f"**Decided At:** {reservation['decided_at']}\n"

            return details
        except Exception as e:
            logger.error(f"Error getting request details: {e}")
            return f"Error retrieving reservation {reservation_id}: {str(e)}"

    def process_admin_decision(
        self,
        reservation_id: int,
        decision: str,
        admin_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process admin decision on a reservation request and update database.

        Args:
            reservation_id: Reservation ID
            decision: 'approved' or 'rejected'
            admin_notes: Optional notes from admin

        Returns:
            Result dictionary with decision details
        """
        if decision not in ['approved', 'rejected']:
            return {
                "success": False,
                "error": "Decision must be 'approved' or 'rejected'"
            }

        try:
            # Check if reservation exists
            reservation = self.db_manager.get_reservation(reservation_id)
            if not reservation:
                return {
                    "success": False,
                    "error": f"Reservation {reservation_id} not found"
                }

            # Update reservation in database
            from sqlalchemy import create_engine, update
            from sqlalchemy.orm import sessionmaker
            from ..database.models import Reservation

            engine = create_engine(self.settings.database_url)
            SessionLocal = sessionmaker(bind=engine)
            session = SessionLocal()

            try:
                # Determine new status based on decision
                new_status = "confirmed" if decision == "approved" else "cancelled"

                stmt = update(Reservation).where(
                    Reservation.id == reservation_id
                ).values(
                    status=new_status,
                    admin_decision=decision,
                    admin_notes=admin_notes,
                    decided_at=datetime.now(),
                    confirmed_by_admin=True
                )

                session.execute(stmt)
                session.commit()

                decided_at = datetime.now()
                logger.info(f"Reservation {reservation_id} {decision} by admin and saved to database")

                # Stage 3: Write approved reservations to file via MCP server
                logger.info(f"[MCP] Check: decision={decision}, use_mcp_server={self.use_mcp_server}, mcp_client={'exists' if self.mcp_client else 'None'}")

                if decision == "approved" and self.use_mcp_server and self.mcp_client:
                    logger.info(f"[MCP] Starting write for reservation {reservation_id}")
                    try:
                        # Convert string dates to datetime objects if needed
                        from dateutil import parser as date_parser
                        start_time = reservation['start_time']
                        end_time = reservation['end_time']

                        if isinstance(start_time, str):
                            start_time = date_parser.parse(start_time)
                        if isinstance(end_time, str):
                            end_time = date_parser.parse(end_time)

                        mcp_result = self.mcp_client.write_reservation(
                            reservation_id=reservation_id,
                            first_name=reservation['first_name'],
                            last_name=reservation['last_name'],
                            car_number=reservation['car_number'],
                            start_time=start_time,
                            end_time=end_time,
                            approval_time=decided_at,
                            admin_notes=admin_notes
                        )

                        logger.info(f"[MCP] Result: {mcp_result}")

                        if mcp_result.get("success"):
                            logger.info(f"[MCP] ✓ Reservation {reservation_id} written to file via MCP server")
                        else:
                            logger.warning(f"[MCP] ✗ Failed to write to MCP server: {mcp_result.get('error')}")
                    except Exception as e:
                        logger.error(f"[MCP] ✗ Exception writing to MCP server: {e}")
                        import traceback
                        logger.error(traceback.format_exc())
                        # Continue even if MCP write fails - database update succeeded
                else:
                    logger.warning(f"[MCP] Write skipped! decision={decision}, use_mcp={self.use_mcp_server}, has_client={self.mcp_client is not None}")

                return {
                    "success": True,
                    "reservation_id": reservation_id,
                    "decision": decision,
                    "admin_notes": admin_notes,
                    "decided_at": decided_at.isoformat(),
                    "mcp_written": decision == "approved" and self.mcp_client is not None
                }
            except Exception as e:
                session.rollback()
                logger.error(f"Database error processing admin decision: {e}")
                return {
                    "success": False,
                    "error": f"Database error: {str(e)}"
                }
            finally:
                session.close()

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
        """Get the current status of a reservation request from database.

        Args:
            reservation_id: Reservation ID

        Returns:
            Reservation status information
        """
        try:
            reservation = self.db_manager.get_reservation(reservation_id)

            if not reservation:
                return None

            return {
                "reservation_id": reservation_id,
                "status": reservation.get("status"),
                "admin_decision": reservation.get("admin_decision"),
                "admin_notes": reservation.get("admin_notes"),
                "decided_at": reservation.get("decided_at")
            }
        except Exception as e:
            logger.error(f"Error getting reservation status: {e}")
            return None
