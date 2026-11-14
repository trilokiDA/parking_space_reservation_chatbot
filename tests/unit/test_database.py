"""Unit tests for database module."""
import pytest
from datetime import datetime, timedelta
from src.database.db_manager import DatabaseManager


@pytest.fixture
def db_manager():
    """Create a test database manager."""
    return DatabaseManager("sqlite:///:memory:")


class TestDatabaseManager:
    """Test cases for DatabaseManager class."""

    def test_initialization(self, db_manager):
        """Test database initialization."""
        assert db_manager is not None
        assert db_manager.engine is not None

    def test_get_dynamic_data(self, db_manager):
        """Test retrieving dynamic data."""
        data = db_manager.get_dynamic_data()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_get_dynamic_data_by_type(self, db_manager):
        """Test retrieving dynamic data by type."""
        availability_data = db_manager.get_dynamic_data("availability")
        assert isinstance(availability_data, list)

        # Check that all records are of type 'availability'
        for record in availability_data:
            assert record["type"] == "availability"

    def test_update_dynamic_data(self, db_manager):
        """Test updating dynamic data."""
        result = db_manager.update_dynamic_data("availability", "available_spaces", "80")
        assert result is True

        # Verify the update
        data = db_manager.get_dynamic_data("availability")
        available_record = next(
            (r for r in data if r["key"] == "available_spaces"),
            None
        )
        assert available_record is not None
        assert available_record["value"] == "80"

    def test_create_reservation(self, db_manager):
        """Test creating a reservation."""
        reservation_data = {
            "first_name": "John",
            "last_name": "Doe",
            "car_number": "ABC123",
            "start_time": datetime.now() + timedelta(days=1),
            "end_time": datetime.now() + timedelta(days=1, hours=3),
            "status": "pending"
        }

        reservation_id = db_manager.create_reservation(reservation_data)
        assert reservation_id is not None
        assert isinstance(reservation_id, int)

    def test_get_reservation(self, db_manager):
        """Test retrieving a reservation."""
        # Create a reservation
        reservation_data = {
            "first_name": "Jane",
            "last_name": "Smith",
            "car_number": "XYZ789",
            "start_time": datetime.now() + timedelta(days=2),
            "end_time": datetime.now() + timedelta(days=2, hours=4),
            "status": "pending"
        }

        reservation_id = db_manager.create_reservation(reservation_data)

        # Retrieve the reservation
        retrieved = db_manager.get_reservation(reservation_id)
        assert retrieved is not None
        assert retrieved["first_name"] == "Jane"
        assert retrieved["last_name"] == "Smith"
        assert retrieved["car_number"] == "XYZ789"
        assert retrieved["status"] == "pending"

    def test_get_nonexistent_reservation(self, db_manager):
        """Test retrieving a non-existent reservation."""
        retrieved = db_manager.get_reservation(99999)
        assert retrieved is None
