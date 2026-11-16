"""
Integration tests for Stage 3 - End-to-end workflow.
Tests the complete flow: User request -> Admin approval -> MCP file write.
"""
import pytest
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import tempfile
import shutil

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.admin_agent.admin_agent_db import AdminAgentDB
from src.database.db_manager import DatabaseManager
from src.mcp_server.mcp_client import MCPClient
from src.config.settings import get_settings
from dotenv import load_dotenv

load_dotenv()


class TestStage3Integration:
    """Integration tests for Stage 3 complete workflow."""

    @pytest.fixture
    def settings(self):
        """Get application settings."""
        return get_settings()

    @pytest.fixture
    def db_manager(self, settings):
        """Create database manager."""
        return DatabaseManager(settings.database_url)

    @pytest.fixture
    def admin_agent(self, settings):
        """Create admin agent with MCP integration."""
        return AdminAgentDB(settings, use_mcp_server=False)  # Disable MCP for unit tests

    @pytest.fixture
    def test_reservation_data(self):
        """Create test reservation data."""
        return {
            "first_name": "Integration",
            "last_name": "Test",
            "car_number": "INT123",
            "start_time": datetime.now() + timedelta(days=1),
            "end_time": datetime.now() + timedelta(days=1, hours=3)
        }

    def test_reservation_creation(self, db_manager, test_reservation_data):
        """Test creating a reservation in the database."""
        # Create reservation
        reservation = db_manager.create_reservation(**test_reservation_data)

        assert reservation is not None
        assert reservation["first_name"] == test_reservation_data["first_name"]
        assert reservation["status"] == "pending"
        assert reservation["confirmed_by_admin"] is False

        # Cleanup
        reservation_id = reservation["id"]
        return reservation_id

    def test_admin_approval_workflow(self, admin_agent, db_manager, test_reservation_data):
        """Test admin approval workflow."""
        # Step 1: Create a pending reservation
        reservation = db_manager.create_reservation(**test_reservation_data)
        reservation_id = reservation["id"]

        # Step 2: Admin checks pending requests
        pending = admin_agent.get_pending_requests()
        assert str(reservation_id) in pending
        assert "Integration Test" in pending

        # Step 3: Admin gets details
        details = admin_agent.get_request_details(reservation_id)
        assert "Integration Test" in details
        assert "INT123" in details

        # Step 4: Admin approves the reservation
        result = admin_agent.process_admin_decision(
            reservation_id=reservation_id,
            decision="approved",
            admin_notes="Integration test approval"
        )

        assert result["success"] is True
        assert result["decision"] == "approved"
        assert result["reservation_id"] == reservation_id

        # Step 5: Verify status updated
        status = admin_agent.get_reservation_status(reservation_id)
        assert status["status"] == "confirmed"
        assert status["admin_decision"] == "approved"

    def test_admin_rejection_workflow(self, admin_agent, db_manager, test_reservation_data):
        """Test admin rejection workflow."""
        # Create a pending reservation
        test_reservation_data["car_number"] = "REJ456"
        reservation = db_manager.create_reservation(**test_reservation_data)
        reservation_id = reservation["id"]

        # Admin rejects the reservation
        result = admin_agent.process_admin_decision(
            reservation_id=reservation_id,
            decision="rejected",
            admin_notes="Integration test rejection"
        )

        assert result["success"] is True
        assert result["decision"] == "rejected"

        # Verify status
        status = admin_agent.get_reservation_status(reservation_id)
        assert status["status"] == "cancelled"
        assert status["admin_decision"] == "rejected"

    def test_mcp_client_write(self, test_reservation_data):
        """Test MCP client write operation (requires MCP server running)."""
        # This test requires the MCP server to be running
        # Skip if server is not available
        mcp_client = MCPClient()

        if not mcp_client.is_server_available():
            pytest.skip("MCP server is not running")

        # Write reservation
        result = mcp_client.write_reservation(
            reservation_id=999,
            first_name=test_reservation_data["first_name"],
            last_name=test_reservation_data["last_name"],
            car_number=test_reservation_data["car_number"],
            start_time=test_reservation_data["start_time"],
            end_time=test_reservation_data["end_time"],
            approval_time=datetime.now(),
            admin_notes="MCP integration test"
        )

        # For offline test, just check structure
        assert "success" in result

    def test_end_to_end_approval_flow(self, admin_agent, db_manager, test_reservation_data):
        """Test complete end-to-end approval flow."""
        # Disable MCP for this test
        admin_agent.use_mcp_server = False

        # Step 1: Customer creates reservation
        test_reservation_data["car_number"] = "E2E789"
        reservation = db_manager.create_reservation(**test_reservation_data)
        reservation_id = reservation["id"]

        # Verify initial state
        assert reservation["status"] == "pending"

        # Step 2: Admin reviews and approves
        result = admin_agent.process_admin_decision(
            reservation_id=reservation_id,
            decision="approved",
            admin_notes="End-to-end test approval"
        )

        assert result["success"] is True

        # Step 3: Verify final state
        final_status = admin_agent.get_reservation_status(reservation_id)
        assert final_status["status"] == "confirmed"
        assert final_status["admin_decision"] == "approved"
        assert final_status["admin_notes"] == "End-to-end test approval"
        assert final_status["decided_at"] is not None


class TestDataIntegrity:
    """Test data integrity across components."""

    @pytest.fixture
    def settings(self):
        """Get application settings."""
        return get_settings()

    @pytest.fixture
    def db_manager(self, settings):
        """Create database manager."""
        return DatabaseManager(settings.database_url)

    def test_reservation_data_consistency(self, db_manager):
        """Test that reservation data remains consistent."""
        # Create reservation
        data = {
            "first_name": "Consistency",
            "last_name": "Check",
            "car_number": "CON999",
            "start_time": datetime.now() + timedelta(days=1),
            "end_time": datetime.now() + timedelta(days=1, hours=2)
        }

        reservation = db_manager.create_reservation(**data)
        reservation_id = reservation["id"]

        # Retrieve and verify
        retrieved = db_manager.get_reservation(reservation_id)
        assert retrieved["first_name"] == data["first_name"]
        assert retrieved["last_name"] == data["last_name"]
        assert retrieved["car_number"] == data["car_number"]

    def test_timestamp_accuracy(self, db_manager):
        """Test that timestamps are accurate."""
        before_create = datetime.now()

        reservation = db_manager.create_reservation(
            first_name="Time",
            last_name="Test",
            car_number="TIME1",
            start_time=datetime.now() + timedelta(days=1),
            end_time=datetime.now() + timedelta(days=1, hours=2)
        )

        after_create = datetime.now()

        # created_at should be between before and after
        created_at = datetime.fromisoformat(str(reservation["created_at"]))
        assert before_create <= created_at <= after_create


class TestErrorHandling:
    """Test error handling in Stage 3 integration."""

    @pytest.fixture
    def settings(self):
        """Get application settings."""
        return get_settings()

    @pytest.fixture
    def admin_agent(self, settings):
        """Create admin agent."""
        return AdminAgentDB(settings, use_mcp_server=False)

    def test_approve_nonexistent_reservation(self, admin_agent):
        """Test approving a reservation that doesn't exist."""
        result = admin_agent.process_admin_decision(
            reservation_id=99999,
            decision="approved"
        )

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_invalid_decision_value(self, admin_agent):
        """Test providing invalid decision value."""
        result = admin_agent.process_admin_decision(
            reservation_id=1,
            decision="invalid_decision"
        )

        assert result["success"] is False
        assert "approved" in result["error"].lower() or "rejected" in result["error"].lower()

    def test_mcp_client_invalid_server(self):
        """Test MCP client with invalid server."""
        client = MCPClient(base_url="http://invalid.server:9999")

        result = client.write_reservation(
            reservation_id=1,
            first_name="Test",
            last_name="User",
            car_number="TEST1",
            start_time=datetime.now(),
            end_time=datetime.now() + timedelta(hours=1)
        )

        assert result["success"] is False
        assert "error" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
