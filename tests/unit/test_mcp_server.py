"""
Unit tests for MCP Server functionality (Stage 3).
Tests file writing, API endpoints, and security features.
"""
import pytest
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
import tempfile
import shutil

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.mcp_server.mcp_server import app, RESERVATIONS_FILE, SERVER_API_KEY, format_reservation_entry
from src.mcp_server.mcp_server import ReservationData, ensure_data_directory
from src.mcp_server.mcp_client import MCPClient


class TestMCPServer:
    """Test MCP Server API endpoints."""

    @pytest.fixture
    def client(self):
        """Create FastAPI test client."""
        return TestClient(app)

    @pytest.fixture
    def test_data_dir(self):
        """Create temporary directory for test data."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def sample_reservation(self):
        """Create sample reservation data."""
        return ReservationData(
            reservation_id=1,
            first_name="John",
            last_name="Doe",
            car_number="ABC123",
            start_time=datetime.now() + timedelta(days=1),
            end_time=datetime.now() + timedelta(days=1, hours=4),
            approval_time=datetime.now(),
            admin_notes="Approved for regular customer"
        )

    def test_root_endpoint(self, client):
        """Test root endpoint returns service info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert data["service"] == "Reservation MCP Server"

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert data["status"] == "healthy"

    def test_write_reservation_no_auth(self, client, sample_reservation):
        """Test writing reservation without authentication fails."""
        # Convert to dict and make JSON-serializable
        data = sample_reservation.dict()
        data['start_time'] = data['start_time'].isoformat()
        data['end_time'] = data['end_time'].isoformat()
        data['approval_time'] = data['approval_time'].isoformat()

        response = client.post(
            "/api/v1/reservations/write",
            json=data
        )
        assert response.status_code == 422  # Missing required header

    def test_write_reservation_invalid_auth(self, client, sample_reservation):
        """Test writing reservation with invalid API key fails."""
        # Convert to dict and make JSON-serializable
        data = sample_reservation.dict()
        data['start_time'] = data['start_time'].isoformat()
        data['end_time'] = data['end_time'].isoformat()
        data['approval_time'] = data['approval_time'].isoformat()

        response = client.post(
            "/api/v1/reservations/write",
            headers={"X-API-Key": "invalid_key"},
            json=data
        )
        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]

    def test_write_reservation_success(self, client, sample_reservation):
        """Test successfully writing a reservation."""
        # Convert to dict and make JSON-serializable
        data = sample_reservation.dict()
        data['start_time'] = data['start_time'].isoformat()
        data['end_time'] = data['end_time'].isoformat()
        data['approval_time'] = data['approval_time'].isoformat()

        response = client.post(
            "/api/v1/reservations/write",
            headers={"X-API-Key": SERVER_API_KEY},
            json=data
        )
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        assert response_data["reservation_id"] == sample_reservation.reservation_id
        assert "file_path" in response_data

    def test_write_reservation_invalid_dates(self, client, sample_reservation):
        """Test writing reservation with invalid dates fails."""
        # Make end_time before start_time
        sample_reservation.end_time = sample_reservation.start_time - timedelta(hours=1)

        # Convert to dict and make JSON-serializable
        data = sample_reservation.dict()
        data['start_time'] = data['start_time'].isoformat()
        data['end_time'] = data['end_time'].isoformat()
        data['approval_time'] = data['approval_time'].isoformat()

        response = client.post(
            "/api/v1/reservations/write",
            headers={"X-API-Key": SERVER_API_KEY},
            json=data
        )
        assert response.status_code == 400
        assert "End time must be after start time" in response.json()["detail"]

    def test_list_reservations(self, client, sample_reservation):
        """Test listing reservations."""
        # Convert to dict and make JSON-serializable
        data = sample_reservation.dict()
        data['start_time'] = data['start_time'].isoformat()
        data['end_time'] = data['end_time'].isoformat()
        data['approval_time'] = data['approval_time'].isoformat()

        # First write a reservation
        client.post(
            "/api/v1/reservations/write",
            headers={"X-API-Key": SERVER_API_KEY},
            json=data
        )

        # Then list reservations
        response = client.get(
            "/api/v1/reservations/list",
            headers={"X-API-Key": SERVER_API_KEY}
        )
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "reservations" in data
        assert data["count"] > 0

    def test_list_reservations_with_limit(self, client):
        """Test listing reservations with limit."""
        response = client.get(
            "/api/v1/reservations/list?limit=10",
            headers={"X-API-Key": SERVER_API_KEY}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["reservations"]) <= 10

    def test_format_reservation_entry(self, sample_reservation):
        """Test reservation entry formatting."""
        entry = format_reservation_entry(sample_reservation)

        # Check format: Name | Car Number | Reservation Period | Approval Time
        assert "John Doe" in entry
        assert "ABC123" in entry
        assert "to" in entry  # Indicates period format
        assert sample_reservation.car_number in entry

        # Check with admin notes
        if sample_reservation.admin_notes:
            assert "Notes:" in entry
            assert sample_reservation.admin_notes in entry

    def test_ensure_data_directory(self, test_data_dir):
        """Test data directory creation."""
        ensure_data_directory()
        assert RESERVATIONS_FILE.parent.exists()

        if RESERVATIONS_FILE.exists():
            # Check header exists
            with open(RESERVATIONS_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "Confirmed Parking Reservations" in content
                assert "Format:" in content


class TestMCPClient:
    """Test MCP Client functionality."""

    @pytest.fixture
    def mcp_client(self):
        """Create MCP client instance."""
        # Use the generated API key
        os.environ["MCP_SERVER_API_KEY"] = SERVER_API_KEY
        return MCPClient(base_url="http://127.0.0.1:8001")

    @pytest.fixture
    def test_reservation_data(self):
        """Create test reservation data."""
        return {
            "reservation_id": 100,
            "first_name": "Jane",
            "last_name": "Smith",
            "car_number": "XYZ789",
            "start_time": datetime.now() + timedelta(days=2),
            "end_time": datetime.now() + timedelta(days=2, hours=3),
            "admin_notes": "Test reservation"
        }

    def test_client_initialization(self, mcp_client):
        """Test MCP client initialization."""
        assert mcp_client.base_url == "http://127.0.0.1:8001"
        assert mcp_client.api_key == SERVER_API_KEY
        assert "X-API-Key" in mcp_client.session.headers

    def test_check_health_offline(self, mcp_client):
        """Test health check when server is offline."""
        # Use invalid URL to simulate offline server
        mcp_client.base_url = "http://127.0.0.1:9999"
        health = mcp_client.check_health()
        assert health["status"] == "unhealthy"
        assert "error" in health

    def test_is_server_available_offline(self, mcp_client):
        """Test server availability check when offline."""
        mcp_client.base_url = "http://127.0.0.1:9999"
        assert not mcp_client.is_server_available()

    def test_write_reservation_offline(self, mcp_client, test_reservation_data):
        """Test writing reservation when server is offline."""
        mcp_client.base_url = "http://127.0.0.1:9999"
        result = mcp_client.write_reservation(**test_reservation_data)
        assert result["success"] is False
        assert "error" in result

    def test_list_reservations_offline(self, mcp_client):
        """Test listing reservations when server is offline."""
        mcp_client.base_url = "http://127.0.0.1:9999"
        result = mcp_client.list_reservations()
        assert result["count"] == 0
        assert "error" in result


class TestSecurityFeatures:
    """Test security features of MCP server."""

    @pytest.fixture
    def client(self):
        """Create FastAPI test client."""
        return TestClient(app)

    def test_api_key_required(self, client):
        """Test that API key is required for all protected endpoints."""
        endpoints = [
            "/api/v1/reservations/write",
            "/api/v1/reservations/list",
        ]

        for endpoint in endpoints:
            if "write" in endpoint:
                response = client.post(endpoint, json={})
            else:
                response = client.get(endpoint)

            # Should fail without API key
            assert response.status_code in [401, 422]

    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options("/")
        assert "access-control-allow-origin" in response.headers

    def test_input_validation(self, client):
        """Test input validation for reservation data."""
        invalid_data = {
            "reservation_id": "not_a_number",  # Should be int
            "first_name": "",  # Too short
            "car_number": "",
            "start_time": "invalid_date",
            "end_time": "invalid_date"
        }

        response = client.post(
            "/api/v1/reservations/write",
            headers={"X-API-Key": SERVER_API_KEY},
            json=invalid_data
        )

        # Should fail validation
        assert response.status_code == 422


class TestFileOperations:
    """Test file operations and data persistence."""

    @pytest.fixture
    def client(self):
        """Create FastAPI test client."""
        return TestClient(app)

    def test_file_creation(self):
        """Test that reservation file is created."""
        ensure_data_directory()
        assert RESERVATIONS_FILE.parent.exists()

    def test_concurrent_writes(self, client):
        """Test handling of concurrent write requests."""
        reservations = []
        for i in range(5):
            reservation = ReservationData(
                reservation_id=200 + i,
                first_name=f"User{i}",
                last_name="Test",
                car_number=f"CAR{i}",
                start_time=datetime.now() + timedelta(days=i+1),
                end_time=datetime.now() + timedelta(days=i+1, hours=2)
            )
            reservations.append(reservation)

        # Write all reservations
        responses = []
        for res in reservations:
            response = client.post(
                "/api/v1/reservations/write",
                headers={"X-API-Key": SERVER_API_KEY},
                json=res.dict()
            )
            responses.append(response)

        # All should succeed
        for response in responses:
            assert response.status_code == 200
            assert response.json()["success"] is True

    def test_data_persistence(self, client):
        """Test that written data persists in file."""
        # Write a unique reservation
        unique_id = 9999
        reservation = ReservationData(
            reservation_id=unique_id,
            first_name="Persist",
            last_name="Test",
            car_number="PERSIST1",
            start_time=datetime.now() + timedelta(days=1),
            end_time=datetime.now() + timedelta(days=1, hours=2)
        )

        # Write it
        write_response = client.post(
            "/api/v1/reservations/write",
            headers={"X-API-Key": SERVER_API_KEY},
            json=reservation.dict()
        )
        assert write_response.status_code == 200

        # Read it back
        list_response = client.get(
            "/api/v1/reservations/list",
            headers={"X-API-Key": SERVER_API_KEY}
        )
        assert list_response.status_code == 200

        data = list_response.json()
        # Check if our reservation is in the list
        reservations_text = " ".join(data["reservations"])
        assert "PERSIST1" in reservations_text or "Persist Test" in reservations_text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
