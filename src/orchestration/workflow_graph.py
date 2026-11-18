"""
LangGraph Orchestration for Intelligent Parking Reservation System.
Stage 4 Implementation - Complete workflow integration.
"""
from typing import Dict, Any, TypedDict, Annotated, Optional
from datetime import datetime
import logging
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from ..config.settings import Settings
from ..chatbot.chatbot import ParkingChatbot
from ..admin_agent.admin_agent_db import AdminAgentDB
from ..mcp_server.mcp_client import MCPClient
from ..database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class ReservationWorkflowState(TypedDict):
    """State for the reservation workflow."""
    # User interaction
    user_message: str
    chatbot_response: str
    conversation_history: list

    # Reservation data
    reservation_id: Optional[int]
    reservation_data: Optional[Dict[str, Any]]

    # Workflow status
    current_stage: str  # "user_interaction", "awaiting_approval", "processing", "completed", "rejected"
    admin_decision: Optional[str]  # "approved", "rejected", or None
    admin_notes: Optional[str]

    # Metadata
    timestamp: str
    error_message: Optional[str]
    retry_count: int


class ReservationOrchestrator:
    """
    LangGraph-based orchestrator for the complete reservation workflow.

    Workflow stages:
    1. User Interaction: RAG chatbot handles user queries and reservation requests
    2. Admin Approval: Human-in-the-loop agent reviews and approves/rejects
    3. MCP Processing: Confirmed reservations written to file via MCP server
    """

    def __init__(self, settings: Settings):
        """
        Initialize the orchestrator.

        Args:
            settings: Application settings
        """
        self.settings = settings

        # Initialize components
        logger.info("Initializing orchestration components...")

        self.chatbot = ParkingChatbot(settings)
        self.admin_agent = AdminAgentDB(settings, use_mcp_server=True)
        self.db_manager = DatabaseManager(settings.database_url)

        # Build the workflow graph
        self.workflow = self._build_workflow_graph()

        logger.info("Orchestrator initialized successfully")

    def _build_workflow_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow.

        Graph structure:
        START -> user_interaction_node -> [decision: is_reservation?]
            -> Yes -> admin_approval_node -> [decision: approved?]
                -> Yes -> mcp_processing_node -> END
                -> No -> user_notification_node -> END
            -> No -> END
        """
        # Define the graph
        workflow = StateGraph(ReservationWorkflowState)

        # Add nodes
        workflow.add_node("user_interaction", self._user_interaction_node)
        workflow.add_node("check_reservation", self._check_reservation_node)
        workflow.add_node("admin_approval", self._admin_approval_node)
        workflow.add_node("mcp_processing", self._mcp_processing_node)
        workflow.add_node("user_notification", self._user_notification_node)

        # Set entry point
        workflow.set_entry_point("user_interaction")

        # Add conditional edges
        workflow.add_conditional_edges(
            "user_interaction",
            self._should_proceed_to_approval,
            {
                "needs_approval": "admin_approval",
                "no_reservation": "check_reservation",
                "completed": END
            }
        )

        workflow.add_conditional_edges(
            "check_reservation",
            self._check_reservation_status,
            {
                "awaiting_approval": "admin_approval",
                "completed": END
            }
        )

        workflow.add_conditional_edges(
            "admin_approval",
            self._check_admin_decision,
            {
                "approved": "mcp_processing",
                "rejected": "user_notification",
                "pending": END
            }
        )

        workflow.add_edge("mcp_processing", "user_notification")
        workflow.add_edge("user_notification", END)

        # Compile with checkpointer for state persistence
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)

    def _user_interaction_node(self, state: ReservationWorkflowState) -> ReservationWorkflowState:
        """
        Handle user interaction through the RAG chatbot.

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state
        """
        logger.info("Processing user interaction...")

        try:
            user_message = state.get("user_message", "")

            # Process message through chatbot
            response = self.chatbot.process_message(user_message)

            # Update conversation history
            history = state.get("conversation_history", [])
            history.append({
                "user": user_message,
                "bot": response,
                "timestamp": datetime.now().isoformat()
            })

            # Check if a reservation was created
            reservation_id = self._extract_reservation_id(response)

            state["chatbot_response"] = response
            state["conversation_history"] = history
            state["timestamp"] = datetime.now().isoformat()

            if reservation_id:
                state["reservation_id"] = reservation_id
                state["current_stage"] = "awaiting_approval"
                logger.info(f"Reservation {reservation_id} created, awaiting approval")
            else:
                state["current_stage"] = "user_interaction"

            return state

        except Exception as e:
            logger.error(f"Error in user interaction: {e}")
            state["error_message"] = str(e)
            state["current_stage"] = "error"
            return state

    def _check_reservation_node(self, state: ReservationWorkflowState) -> ReservationWorkflowState:
        """
        Check if there's a reservation to track.

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state
        """
        logger.info("Checking reservation status...")

        try:
            # Extract reservation ID from user message if status check
            user_message = state.get("user_message", "").lower()

            if "status" in user_message or "check" in user_message:
                import re
                match = re.search(r'\d+', user_message)
                if match:
                    reservation_id = int(match.group())
                    state["reservation_id"] = reservation_id

                    # Get reservation from database
                    reservation = self.db_manager.get_reservation(reservation_id)
                    if reservation:
                        state["reservation_data"] = {
                            "id": reservation.id,
                            "status": reservation.status,
                            "first_name": reservation.first_name,
                            "last_name": reservation.last_name,
                            "car_number": reservation.car_number,
                            "start_time": reservation.start_time,
                            "end_time": reservation.end_time
                        }
                        state["current_stage"] = reservation.status
                        logger.info(f"Reservation {reservation_id} status: {reservation.status}")

            return state

        except Exception as e:
            logger.error(f"Error checking reservation: {e}")
            state["error_message"] = str(e)
            return state

    def _admin_approval_node(self, state: ReservationWorkflowState) -> ReservationWorkflowState:
        """
        Handle admin approval process.

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state
        """
        logger.info("Processing admin approval...")

        try:
            reservation_id = state.get("reservation_id")
            if not reservation_id:
                logger.warning("No reservation ID found in state")
                return state

            # Get reservation from database
            reservation = self.db_manager.get_reservation(reservation_id)
            if not reservation:
                logger.error(f"Reservation {reservation_id} not found")
                state["error_message"] = "Reservation not found"
                return state

            # Check current status
            if reservation.status == "approved":
                state["admin_decision"] = "approved"
                state["current_stage"] = "processing"
                state["reservation_data"] = {
                    "id": reservation.id,
                    "first_name": reservation.first_name,
                    "last_name": reservation.last_name,
                    "car_number": reservation.car_number,
                    "start_time": reservation.start_time,
                    "end_time": reservation.end_time,
                    "admin_notes": reservation.admin_notes
                }
                logger.info(f"Reservation {reservation_id} approved")

            elif reservation.status == "rejected":
                state["admin_decision"] = "rejected"
                state["current_stage"] = "rejected"
                state["admin_notes"] = reservation.admin_notes
                logger.info(f"Reservation {reservation_id} rejected")

            else:
                # Still pending
                state["admin_decision"] = None
                state["current_stage"] = "awaiting_approval"
                logger.info(f"Reservation {reservation_id} still pending")

            return state

        except Exception as e:
            logger.error(f"Error in admin approval: {e}")
            state["error_message"] = str(e)
            return state

    def _mcp_processing_node(self, state: ReservationWorkflowState) -> ReservationWorkflowState:
        """
        Process confirmed reservation through MCP server.

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state
        """
        logger.info("Processing through MCP server...")

        try:
            reservation_data = state.get("reservation_data")
            if not reservation_data:
                logger.error("No reservation data found")
                state["error_message"] = "No reservation data"
                return state

            # Write to MCP server via admin agent
            if self.admin_agent.mcp_client:
                try:
                    result = self.admin_agent.mcp_client.write_reservation(
                        reservation_id=reservation_data["id"],
                        first_name=reservation_data["first_name"],
                        last_name=reservation_data["last_name"],
                        car_number=reservation_data["car_number"],
                        start_time=reservation_data["start_time"],
                        end_time=reservation_data["end_time"],
                        approval_time=datetime.now(),
                        admin_notes=reservation_data.get("admin_notes")
                    )

                    if result.get("success"):
                        state["current_stage"] = "completed"
                        logger.info(f"Reservation {reservation_data['id']} written to file successfully")
                    else:
                        state["error_message"] = "Failed to write to MCP server"
                        logger.error(f"MCP write failed: {result}")

                except Exception as e:
                    logger.error(f"MCP client error: {e}")
                    state["error_message"] = f"MCP error: {str(e)}"
            else:
                logger.warning("MCP client not available, skipping file write")
                state["current_stage"] = "completed"

            return state

        except Exception as e:
            logger.error(f"Error in MCP processing: {e}")
            state["error_message"] = str(e)
            return state

    def _user_notification_node(self, state: ReservationWorkflowState) -> ReservationWorkflowState:
        """
        Send notification to user about final status.

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state
        """
        logger.info("Sending user notification...")

        try:
            current_stage = state.get("current_stage")
            reservation_id = state.get("reservation_id")

            if current_stage == "completed":
                notification = f"✅ Reservation {reservation_id} has been approved and confirmed! Your parking space is reserved."
            elif current_stage == "rejected":
                admin_notes = state.get("admin_notes", "No reason provided")
                notification = f"❌ Reservation {reservation_id} was rejected. Reason: {admin_notes}"
            else:
                notification = f"ℹ️ Reservation {reservation_id} status: {current_stage}"

            state["chatbot_response"] = notification
            logger.info(f"Notification sent: {notification}")

            return state

        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            state["error_message"] = str(e)
            return state

    def _should_proceed_to_approval(self, state: ReservationWorkflowState) -> str:
        """
        Decide if we should proceed to admin approval.

        Args:
            state: Current workflow state

        Returns:
            Next node: "needs_approval", "no_reservation", or "completed"
        """
        current_stage = state.get("current_stage", "")
        reservation_id = state.get("reservation_id")

        if reservation_id and current_stage == "awaiting_approval":
            return "needs_approval"
        elif "status" in state.get("user_message", "").lower() or "check" in state.get("user_message", "").lower():
            return "no_reservation"
        else:
            return "completed"

    def _check_reservation_status(self, state: ReservationWorkflowState) -> str:
        """
        Check reservation status after lookup.

        Args:
            state: Current workflow state

        Returns:
            Next node: "awaiting_approval" or "completed"
        """
        current_stage = state.get("current_stage", "")

        if current_stage in ["pending", "awaiting_approval"]:
            return "awaiting_approval"
        else:
            return "completed"

    def _check_admin_decision(self, state: ReservationWorkflowState) -> str:
        """
        Check admin decision.

        Args:
            state: Current workflow state

        Returns:
            Next node: "approved", "rejected", or "pending"
        """
        admin_decision = state.get("admin_decision")

        if admin_decision == "approved":
            return "approved"
        elif admin_decision == "rejected":
            return "rejected"
        else:
            return "pending"

    def _extract_reservation_id(self, response: str) -> Optional[int]:
        """
        Extract reservation ID from chatbot response.

        Args:
            response: Chatbot response text

        Returns:
            Reservation ID if found, None otherwise
        """
        import re

        # Look for patterns like "Reservation ID: 123"
        patterns = [
            r"Reservation ID:\s*(\d+)",
            r"reservation\s+(\d+)",
            r"ID:\s*(\d+)"
        ]

        for pattern in patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                return int(match.group(1))

        return None

    def process_user_input(self, user_message: str, thread_id: str = "default") -> Dict[str, Any]:
        """
        Process user input through the complete workflow.

        Args:
            user_message: User's message
            thread_id: Thread ID for conversation persistence

        Returns:
            Final workflow state
        """
        logger.info(f"Processing user input: {user_message}")

        # Initial state
        initial_state = {
            "user_message": user_message,
            "chatbot_response": "",
            "conversation_history": [],
            "reservation_id": None,
            "reservation_data": None,
            "current_stage": "user_interaction",
            "admin_decision": None,
            "admin_notes": None,
            "timestamp": datetime.now().isoformat(),
            "error_message": None,
            "retry_count": 0
        }

        # Run the workflow
        config = {"configurable": {"thread_id": thread_id}}

        try:
            result = self.workflow.invoke(initial_state, config)
            logger.info(f"Workflow completed. Stage: {result.get('current_stage')}")
            return result

        except Exception as e:
            logger.error(f"Workflow error: {e}")
            return {
                **initial_state,
                "error_message": str(e),
                "current_stage": "error"
            }

    def get_workflow_status(self, reservation_id: int) -> Dict[str, Any]:
        """
        Get current status of a reservation workflow.

        Args:
            reservation_id: Reservation ID to check

        Returns:
            Status information
        """
        try:
            reservation = self.db_manager.get_reservation(reservation_id)

            if not reservation:
                return {
                    "found": False,
                    "message": f"Reservation {reservation_id} not found"
                }

            return {
                "found": True,
                "reservation_id": reservation.id,
                "status": reservation.status,
                "first_name": reservation.first_name,
                "last_name": reservation.last_name,
                "car_number": reservation.car_number,
                "start_time": reservation.start_time.isoformat() if reservation.start_time else None,
                "end_time": reservation.end_time.isoformat() if reservation.end_time else None,
                "admin_notes": reservation.admin_notes,
                "created_at": reservation.created_at.isoformat() if reservation.created_at else None
            }

        except Exception as e:
            logger.error(f"Error getting workflow status: {e}")
            return {
                "found": False,
                "error": str(e)
            }
