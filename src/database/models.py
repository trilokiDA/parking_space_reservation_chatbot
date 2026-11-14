"""Database models for dynamic data storage."""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

Base = declarative_base()


class DynamicData(Base):
    """Model for storing dynamic parking information."""

    __tablename__ = "dynamic_data"

    id = Column(Integer, primary_key=True, index=True)
    data_type = Column(String, nullable=False, index=True)  # e.g., 'availability', 'price', 'hours'
    key = Column(String, nullable=False, index=True)
    value = Column(String, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<DynamicData(type={self.data_type}, key={self.key}, value={self.value})>"


class Reservation(Base):
    """Model for storing reservation information."""

    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    car_number = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    parking_space = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending, confirmed, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    confirmed_by_admin = Column(Boolean, default=False)

    def __repr__(self):
        return f"<Reservation(id={self.id}, name={self.first_name} {self.last_name}, status={self.status})>"
