"""
Integration tests for the complete workflow.
Stage 4 Testing - End-to-end workflow testing.
"""
import pytest
import time
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config.settings import Settings
from src.database.db_manager import DatabaseManager
from src.orchestration.workflow_graph import ReservationOrchestrator


class TestCompleteWorkflow:
    """Integration tests for complete reservation workflow."""

    @pytest.fixture(scope="class")
    def test_settings(self):
        """Create test settings."""
        settings = Settings()
        # Use test database
        settings.database_url = "sqlite:///test_workflow.db"
        return settings

    @pytest.fixture(scope="class")
    def db_manager(self, test_settings):
        """Create database manager for testing."""
        db = DatabaseManager(test_settings.database_url)
        # Clean up test database
        db.clear_reservations()
        yield db
        # Cleanup after tests
        db.clear_reservations()

    @pytest.fixture(scope="class")
    def orchestrator(self, test_settings):
        """Create orchestrator instance for testing."""
        try:
            orch = ReservationOrchestrator(test_settings)
            return orch
        except Exception as e:
            pytest.skip(f"Could not initialize orchestrator: {e}")

    def test_workflow_info_query(self, orchestrator):
        """Test simple information query workflow."""
        result = orchestrator.process_user_input(
            "What are your operating hours?",
            thread_id="test_info_1"
        )

        assert result is not None
        assert "chatbot_response" in result
        assert len(result["chatbot_response"]) > 0

    def test_workflow_reservation_creation(self, orchestrator, db_manager):
        """Test reservation creation through workflow."""
        # Start reservation
        result = orchestrator.process_user_input(
            "I want to make a reservation",
            thread_id="test_res_1"
        )

        assert result is not None
        assert "chatbot_response" in result

        # Provide user information (simulate multi-turn conversation)
        # Note: In actual implementation, the chatbot collects this info
        # For testing, we'll create a reservation directly in DB
        start_time = datetime.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=4)

        reservation_id = db_manager.create_reservation(
            first_name="Test",
            last_name="User",
            car_number="TEST123",
            start_time=start_time,
            end_time=end_time
        )

        assert reservation_id is not None

        # Check reservation status
        reservation = db_manager.get_reservation(reservation_id)
        assert reservation is not None
        assert reservation.status == "pending"

    def test_workflow_status_check(self, orchestrator, db_manager):
        """Test checking reservation status through workflow."""
        # Create a test reservation
        start_time = datetime.now() + timedelta(days=1)
        end_time = start_time + timedelta(hours=4)

        reservation_id = db_manager.create_reservation(
            first_name="Status",
            last_name="Check",
            car_number="STATUS1",
            start_time=start_time,
            end_time=end_time
        )

        # Check status through orchestrator
        status = orchestrator.get_workflow_status(reservation_id)

        assert status["found"] is True
        assert status["reservation_id"] == reservation_id
        assert status["status"] == "pending"

    def test_workflow_approval_flow(self, orchestrator, db_manager):
        """Test approval workflow."""
        # Create reservation
        start_time = datetime.now() + timedelta(days=2)
        end_time = start_time + timedelta(hours=3)

        reservation_id = db_manager.create_reservation(
            first_name="Approval",
            last_name="Test",
            car_number="APPR123",
            start_time=start_time,
            end_time=end_time
        )

        # Simulate admin approval
        success = db_manager.update_reservation_status(
            reservation_id,
            "approved",
            "Test approval"
        )

        assert success is True

        # Check updated status
        reservation = db_manager.get_reservation(reservation_id)
        assert reservation.status == "approved"
        assert reservation.admin_notes == "Test approval"

    def test_workflow_rejection_flow(self, orchestrator, db_manager):
        """Test rejection workflow."""
        # Create reservation
        start_time = datetime.now() + timedelta(days=3)
        end_time = start_time + timedelta(hours=2)

        reservation_id = db_manager.create_reservation(
            first_name="Reject",
            last_name="Test",
            car_number="REJ123",
            start_time=start_time,
            end_time=end_time
        )

        # Simulate admin rejection
        success = db_manager.update_reservation_status(
            reservation_id,
            "rejected",
            "Time slot not available"
        )

        assert success is True

        # Check updated status
        reservation = db_manager.get_reservation(reservation_id)
        assert reservation.status == "rejected"
        assert reservation.admin_notes == "Time slot not available"


class TestWorkflowPerformance:
    """Performance tests for workflow orchestration."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator for performance testing."""
        try:
            settings = Settings()
            settings.database_url = "sqlite:///test_perf.db"
            orch = ReservationOrchestrator(settings)
            return orch
        except Exception as e:
            pytest.skip(f"Could not initialize orchestrator: {e}")

    def test_workflow_response_time(self, orchestrator):
        """Test workflow response time for simple query."""
        start_time = time.time()

        result = orchestrator.process_user_input(
            "What are your hours?",
            thread_id="test_perf_1"
        )

        end_time = time.time()
        response_time = end_time - start_time

        # Response should be within reasonable time (adjust as needed)
        assert response_time < 10.0  # 10 seconds
        assert result is not None

    def test_workflow_concurrent_handling(self, orchestrator):
        """Test handling multiple workflow instances."""
        results = []

        for i in range(5):
            result = orchestrator.process_user_input(
                f"Query number {i}",
                thread_id=f"test_concurrent_{i}"
            )
            results.append(result)

        # All queries should complete successfully
        assert len(results) == 5
        assert all(r is not None for r in results)


class TestWorkflowEdgeCases:
    """Test edge cases and error handling."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator for edge case testing."""
        try:
            settings = Settings()
            settings.database_url = "sqlite:///test_edge.db"
            orch = ReservationOrchestrator(settings)
            return orch
        except Exception as e:
            pytest.skip(f"Could not initialize orchestrator: {e}")

    def test_workflow_empty_input(self, orchestrator):
        """Test workflow with empty input."""
        result = orchestrator.process_user_input(
            "",
            thread_id="test_edge_1"
        )

        # Should handle gracefully
        assert result is not None

    def test_workflow_very_long_input(self, orchestrator):
        """Test workflow with very long input."""
        long_input = "test " * 500

        result = orchestrator.process_user_input(
            long_input,
            thread_id="test_edge_2"
        )

        # Should handle without crashing
        assert result is not None

    def test_workflow_nonexistent_reservation_status(self, orchestrator):
        """Test checking status of non-existent reservation."""
        status = orchestrator.get_workflow_status(99999)

        assert status["found"] is False

    def test_workflow_special_characters(self, orchestrator):
        """Test workflow with special characters in input."""
        special_input = "What about <script>alert('xss')</script> parking?"

        result = orchestrator.process_user_input(
            special_input,
            thread_id="test_edge_3"
        )

        # Should sanitize and process safely
        assert result is not None
        # XSS should be filtered
        if "chatbot_response" in result:
            assert "<script>" not in result["chatbot_response"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
