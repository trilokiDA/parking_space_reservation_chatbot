"""
Unit tests for LangGraph orchestration module.
Stage 4 Testing - Workflow graph and orchestrator.
"""
import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from src.orchestration.workflow_graph import ReservationOrchestrator, ReservationWorkflowState


class TestReservationOrchestrator:
    """Test suite for ReservationOrchestrator."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        settings = Mock()
        settings.database_url = "sqlite:///test.db"
        settings.admin_api_url = "http://localhost:8000"
        settings.openai_api_key = "test-key"
        settings.vector_store_path = "test_vectorstore"
        settings.embedding_model = "text-embedding-3-small"
        settings.llm_model = "gpt-3.5-turbo"
        settings.llm_temperature = 0.7
        settings.max_tokens = 500
        settings.chunk_size = 500
        settings.chunk_overlap = 50
        settings.retrieval_k = 3
        settings.get_active_provider = Mock(return_value="openai")
        settings.get_active_api_key = Mock(return_value="test-key")
        return settings

    @pytest.fixture
    def orchestrator(self, mock_settings):
        """Create orchestrator instance with mocked components."""
        with patch('src.orchestration.workflow_graph.ParkingChatbot'), \
             patch('src.orchestration.workflow_graph.AdminAgentDB'), \
             patch('src.orchestration.workflow_graph.DatabaseManager'):

            orch = ReservationOrchestrator(mock_settings)

            # Mock the components
            orch.chatbot = Mock()
            orch.admin_agent = Mock()
            orch.db_manager = Mock()

            return orch

    def test_orchestrator_initialization(self, mock_settings):
        """Test orchestrator initialization."""
        with patch('src.orchestration.workflow_graph.ParkingChatbot'), \
             patch('src.orchestration.workflow_graph.AdminAgentDB'), \
             patch('src.orchestration.workflow_graph.DatabaseManager'):

            orch = ReservationOrchestrator(mock_settings)

            assert orch.settings == mock_settings
            assert orch.workflow is not None

    def test_user_interaction_node_normal_message(self, orchestrator):
        """Test user interaction node with normal message."""
        state = {
            "user_message": "What are your operating hours?",
            "conversation_history": [],
            "current_stage": "user_interaction"
        }

        orchestrator.chatbot.process_message.return_value = "We operate 24/7."

        result = orchestrator._user_interaction_node(state)

        assert result["chatbot_response"] == "We operate 24/7."
        assert len(result["conversation_history"]) == 1
        assert result["conversation_history"][0]["user"] == "What are your operating hours?"
        assert result["conversation_history"][0]["bot"] == "We operate 24/7."

    def test_user_interaction_node_reservation_created(self, orchestrator):
        """Test user interaction node when reservation is created."""
        state = {
            "user_message": "I want to make a reservation",
            "conversation_history": [],
            "current_stage": "user_interaction"
        }

        orchestrator.chatbot.process_message.return_value = "Reservation created successfully! Reservation ID: 123"

        result = orchestrator._user_interaction_node(state)

        assert result["reservation_id"] == 123
        assert result["current_stage"] == "awaiting_approval"

    def test_extract_reservation_id_various_formats(self, orchestrator):
        """Test extraction of reservation ID from various response formats."""
        test_cases = [
            ("Reservation ID: 123", 123),
            ("Your reservation 456 has been created", 456),
            ("ID: 789", 789),
            ("No reservation here", None),
        ]

        for response, expected_id in test_cases:
            result = orchestrator._extract_reservation_id(response)
            assert result == expected_id

    def test_check_reservation_node(self, orchestrator):
        """Test check reservation node."""
        state = {
            "user_message": "Check status of reservation 123",
            "current_stage": "user_interaction"
        }

        mock_reservation = Mock()
        mock_reservation.id = 123
        mock_reservation.status = "pending"
        mock_reservation.first_name = "John"
        mock_reservation.last_name = "Doe"
        mock_reservation.car_number = "ABC123"
        mock_reservation.start_time = datetime.now()
        mock_reservation.end_time = datetime.now()

        orchestrator.db_manager.get_reservation.return_value = mock_reservation

        result = orchestrator._check_reservation_node(state)

        assert result["reservation_id"] == 123
        assert result["reservation_data"]["status"] == "pending"

    def test_admin_approval_node_approved(self, orchestrator):
        """Test admin approval node with approved reservation."""
        state = {
            "reservation_id": 123,
            "current_stage": "awaiting_approval"
        }

        mock_reservation = Mock()
        mock_reservation.id = 123
        mock_reservation.status = "approved"
        mock_reservation.first_name = "John"
        mock_reservation.last_name = "Doe"
        mock_reservation.car_number = "ABC123"
        mock_reservation.start_time = datetime.now()
        mock_reservation.end_time = datetime.now()
        mock_reservation.admin_notes = "Looks good"

        orchestrator.db_manager.get_reservation.return_value = mock_reservation

        result = orchestrator._admin_approval_node(state)

        assert result["admin_decision"] == "approved"
        assert result["current_stage"] == "processing"

    def test_admin_approval_node_rejected(self, orchestrator):
        """Test admin approval node with rejected reservation."""
        state = {
            "reservation_id": 123,
            "current_stage": "awaiting_approval"
        }

        mock_reservation = Mock()
        mock_reservation.id = 123
        mock_reservation.status = "rejected"
        mock_reservation.admin_notes = "Time slot not available"

        orchestrator.db_manager.get_reservation.return_value = mock_reservation

        result = orchestrator._admin_approval_node(state)

        assert result["admin_decision"] == "rejected"
        assert result["current_stage"] == "rejected"
        assert result["admin_notes"] == "Time slot not available"

    def test_mcp_processing_node_success(self, orchestrator):
        """Test MCP processing node with successful write."""
        state = {
            "reservation_data": {
                "id": 123,
                "first_name": "John",
                "last_name": "Doe",
                "car_number": "ABC123",
                "start_time": datetime.now(),
                "end_time": datetime.now(),
                "admin_notes": "Approved"
            },
            "current_stage": "processing"
        }

        orchestrator.admin_agent.mcp_client = Mock()
        orchestrator.admin_agent.mcp_client.write_reservation.return_value = {
            "success": True
        }

        result = orchestrator._mcp_processing_node(state)

        assert result["current_stage"] == "completed"
        assert orchestrator.admin_agent.mcp_client.write_reservation.called

    def test_mcp_processing_node_failure(self, orchestrator):
        """Test MCP processing node with failed write."""
        state = {
            "reservation_data": {
                "id": 123,
                "first_name": "John",
                "last_name": "Doe",
                "car_number": "ABC123",
                "start_time": datetime.now(),
                "end_time": datetime.now()
            },
            "current_stage": "processing"
        }

        orchestrator.admin_agent.mcp_client = Mock()
        orchestrator.admin_agent.mcp_client.write_reservation.return_value = {
            "success": False
        }

        result = orchestrator._mcp_processing_node(state)

        assert result["error_message"] == "Failed to write to MCP server"

    def test_user_notification_node_completed(self, orchestrator):
        """Test user notification node for completed reservation."""
        state = {
            "current_stage": "completed",
            "reservation_id": 123
        }

        result = orchestrator._user_notification_node(state)

        assert "approved and confirmed" in result["chatbot_response"].lower()

    def test_user_notification_node_rejected(self, orchestrator):
        """Test user notification node for rejected reservation."""
        state = {
            "current_stage": "rejected",
            "reservation_id": 123,
            "admin_notes": "Time slot unavailable"
        }

        result = orchestrator._user_notification_node(state)

        assert "rejected" in result["chatbot_response"].lower()
        assert "Time slot unavailable" in result["chatbot_response"]

    def test_should_proceed_to_approval_with_reservation(self, orchestrator):
        """Test routing decision with new reservation."""
        state = {
            "reservation_id": 123,
            "current_stage": "awaiting_approval",
            "user_message": "I want to make a reservation"
        }

        result = orchestrator._should_proceed_to_approval(state)

        assert result == "needs_approval"

    def test_should_proceed_to_approval_status_check(self, orchestrator):
        """Test routing decision for status check."""
        state = {
            "reservation_id": None,
            "current_stage": "user_interaction",
            "user_message": "Check status of reservation 123"
        }

        result = orchestrator._should_proceed_to_approval(state)

        assert result == "no_reservation"

    def test_check_admin_decision_approved(self, orchestrator):
        """Test admin decision routing for approved."""
        state = {
            "admin_decision": "approved"
        }

        result = orchestrator._check_admin_decision(state)

        assert result == "approved"

    def test_check_admin_decision_rejected(self, orchestrator):
        """Test admin decision routing for rejected."""
        state = {
            "admin_decision": "rejected"
        }

        result = orchestrator._check_admin_decision(state)

        assert result == "rejected"

    def test_check_admin_decision_pending(self, orchestrator):
        """Test admin decision routing for pending."""
        state = {
            "admin_decision": None
        }

        result = orchestrator._check_admin_decision(state)

        assert result == "pending"

    def test_get_workflow_status_found(self, orchestrator):
        """Test getting workflow status for existing reservation."""
        mock_reservation = Mock()
        mock_reservation.id = 123
        mock_reservation.status = "approved"
        mock_reservation.first_name = "John"
        mock_reservation.last_name = "Doe"
        mock_reservation.car_number = "ABC123"
        mock_reservation.start_time = datetime(2024, 12, 25, 14, 0)
        mock_reservation.end_time = datetime(2024, 12, 25, 18, 0)
        mock_reservation.admin_notes = "Approved"
        mock_reservation.created_at = datetime.now()

        orchestrator.db_manager.get_reservation.return_value = mock_reservation

        result = orchestrator.get_workflow_status(123)

        assert result["found"] is True
        assert result["reservation_id"] == 123
        assert result["status"] == "approved"

    def test_get_workflow_status_not_found(self, orchestrator):
        """Test getting workflow status for non-existent reservation."""
        orchestrator.db_manager.get_reservation.return_value = None

        result = orchestrator.get_workflow_status(999)

        assert result["found"] is False
        assert "not found" in result["message"].lower()


class TestWorkflowStateTransitions:
    """Test workflow state transitions and edge cases."""

    def test_state_initialization(self):
        """Test initial state structure."""
        state: ReservationWorkflowState = {
            "user_message": "test",
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

        assert state["current_stage"] == "user_interaction"
        assert state["reservation_id"] is None
        assert state["admin_decision"] is None

    def test_error_handling_in_state(self):
        """Test error message handling in state."""
        state: ReservationWorkflowState = {
            "user_message": "test",
            "chatbot_response": "",
            "conversation_history": [],
            "reservation_id": None,
            "reservation_data": None,
            "current_stage": "error",
            "admin_decision": None,
            "admin_notes": None,
            "timestamp": datetime.now().isoformat(),
            "error_message": "Test error",
            "retry_count": 1
        }

        assert state["error_message"] == "Test error"
        assert state["current_stage"] == "error"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
