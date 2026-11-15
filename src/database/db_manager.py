"""Database manager for handling dynamic data operations."""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .models import Base, DynamicData, Reservation

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manager for database operations."""

    def __init__(self, database_url: str):
        """Initialize database manager.

        Args:
            database_url: SQLAlchemy database URL
        """
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self._initialize_database()

    def _initialize_database(self):
        """Create database tables and populate with initial data."""
        Base.metadata.create_all(bind=self.engine)
        self._populate_initial_data()

    def _populate_initial_data(self):
        """Populate database with initial dynamic data."""
        session = self.SessionLocal()
        try:
            # Check if data already exists
            if session.query(DynamicData).count() > 0:
                return

            # Initial availability data
            availability_data = [
                DynamicData(data_type="availability", key="total_spaces", value="100"),
                DynamicData(data_type="availability", key="available_spaces", value="75"),
                DynamicData(data_type="availability", key="occupied_spaces", value="25"),
            ]

            # Working hours
            hours_data = [
                DynamicData(data_type="hours", key="weekday_open", value="06:00"),
                DynamicData(data_type="hours", key="weekday_close", value="22:00"),
                DynamicData(data_type="hours", key="weekend_open", value="08:00"),
                DynamicData(data_type="hours", key="weekend_close", value="20:00"),
            ]

            # Pricing information
            price_data = [
                DynamicData(data_type="price", key="hourly_rate", value="5.00"),
                DynamicData(data_type="price", key="daily_rate", value="35.00"),
                DynamicData(data_type="price", key="weekly_rate", value="200.00"),
                DynamicData(data_type="price", key="monthly_rate", value="700.00"),
            ]

            session.add_all(availability_data + hours_data + price_data)
            session.commit()
            logger.info("Initial dynamic data populated successfully")
        except Exception as e:
            session.rollback()
            logger.error(f"Error populating initial data: {e}")
        finally:
            session.close()

    def get_dynamic_data(self, data_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve dynamic data from database.

        Args:
            data_type: Optional filter by data type

        Returns:
            List of dynamic data records
        """
        session = self.SessionLocal()
        try:
            query = session.query(DynamicData)
            if data_type:
                query = query.filter(DynamicData.data_type == data_type)

            results = query.all()
            return [
                {
                    "type": r.data_type,
                    "key": r.key,
                    "value": r.value,
                    "updated_at": r.updated_at.isoformat()
                }
                for r in results
            ]
        finally:
            session.close()

    def update_dynamic_data(self, data_type: str, key: str, value: str) -> bool:
        """Update dynamic data value.

        Args:
            data_type: Type of data
            key: Data key
            value: New value

        Returns:
            True if successful, False otherwise
        """
        session = self.SessionLocal()
        try:
            record = session.query(DynamicData).filter(
                DynamicData.data_type == data_type,
                DynamicData.key == key
            ).first()

            if record:
                record.value = value
                record.updated_at = datetime.utcnow()
            else:
                record = DynamicData(data_type=data_type, key=key, value=value)
                session.add(record)

            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating dynamic data: {e}")
            return False
        finally:
            session.close()

    def create_reservation(self, reservation_data: Dict[str, Any]) -> Optional[int]:
        """Create a new reservation.

        Args:
            reservation_data: Reservation information

        Returns:
            Reservation ID if successful, None otherwise
        """
        session = self.SessionLocal()
        try:
            reservation = Reservation(**reservation_data)
            session.add(reservation)
            session.commit()
            session.refresh(reservation)
            logger.info(f"Reservation created with ID: {reservation.id}")
            return reservation.id
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating reservation: {e}")
            return None
        finally:
            session.close()

    def get_reservation(self, reservation_id: int) -> Optional[Dict[str, Any]]:
        """Get reservation by ID.

        Args:
            reservation_id: Reservation ID

        Returns:
            Reservation data if found
        """
        session = self.SessionLocal()
        try:
            reservation = session.query(Reservation).filter(
                Reservation.id == reservation_id
            ).first()

            if reservation:
                return {
                    "id": reservation.id,
                    "first_name": reservation.first_name,
                    "last_name": reservation.last_name,
                    "car_number": reservation.car_number,
                    "start_time": reservation.start_time.isoformat(),
                    "end_time": reservation.end_time.isoformat(),
                    "status": reservation.status,
                    "confirmed_by_admin": reservation.confirmed_by_admin,
                    "admin_decision": reservation.admin_decision,
                    "admin_notes": reservation.admin_notes,
                    "decided_at": reservation.decided_at.isoformat() if reservation.decided_at else None
                }
            return None
        finally:
            session.close()

    def get_all_reservations(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all reservations, optionally filtered by status.

        Args:
            status: Optional status filter (e.g., 'pending', 'confirmed')

        Returns:
            List of reservation data
        """
        session = self.SessionLocal()
        try:
            query = session.query(Reservation)
            if status:
                query = query.filter(Reservation.status == status)

            reservations = query.order_by(Reservation.created_at.desc()).all()

            return [
                {
                    "id": r.id,
                    "first_name": r.first_name,
                    "last_name": r.last_name,
                    "car_number": r.car_number,
                    "start_time": r.start_time.isoformat(),
                    "end_time": r.end_time.isoformat(),
                    "status": r.status,
                    "confirmed_by_admin": r.confirmed_by_admin,
                    "admin_decision": r.admin_decision,
                    "admin_notes": r.admin_notes,
                    "decided_at": r.decided_at.isoformat() if r.decided_at else None,
                    "created_at": r.created_at.isoformat()
                }
                for r in reservations
            ]
        finally:
            session.close()
