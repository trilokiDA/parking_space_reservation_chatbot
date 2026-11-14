"""Input validator for user input validation and sanitization."""
import logging
import re
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class InputValidator:
    """Validator for user input validation and sanitization."""

    def __init__(self):
        """Initialize input validator."""
        self.car_number_pattern = re.compile(r'^[A-Z0-9\-\s]{3,15}$', re.IGNORECASE)
        self.name_pattern = re.compile(r'^[A-Za-z\s\-\']{2,50}$')
        self.dangerous_patterns = [
            r'<script',
            r'javascript:',
            r'onerror=',
            r'onclick=',
            r'DROP\s+TABLE',
            r'DELETE\s+FROM',
            r'INSERT\s+INTO',
            r'UPDATE\s+.*SET'
        ]

    def validate_name(self, name: str) -> Dict[str, Any]:
        """Validate name input.

        Args:
            name: Name to validate

        Returns:
            Validation result with status and message
        """
        if not name or not name.strip():
            return {"valid": False, "message": "Name cannot be empty"}

        name = name.strip()

        if len(name) < 2:
            return {"valid": False, "message": "Name must be at least 2 characters"}

        if len(name) > 50:
            return {"valid": False, "message": "Name must be less than 50 characters"}

        if not self.name_pattern.match(name):
            return {"valid": False, "message": "Name contains invalid characters"}

        return {"valid": True, "message": "Valid name", "sanitized": name}

    def validate_car_number(self, car_number: str) -> Dict[str, Any]:
        """Validate car number input.

        Args:
            car_number: Car number to validate

        Returns:
            Validation result with status and message
        """
        if not car_number or not car_number.strip():
            return {"valid": False, "message": "Car number cannot be empty"}

        car_number = car_number.strip().upper()

        if len(car_number) < 3:
            return {"valid": False, "message": "Car number must be at least 3 characters"}

        if len(car_number) > 15:
            return {"valid": False, "message": "Car number must be less than 15 characters"}

        if not self.car_number_pattern.match(car_number):
            return {"valid": False, "message": "Car number contains invalid characters"}

        return {"valid": True, "message": "Valid car number", "sanitized": car_number}

    def validate_datetime(self, datetime_str: str) -> Dict[str, Any]:
        """Validate datetime input.

        Args:
            datetime_str: Datetime string to validate

        Returns:
            Validation result with status and message
        """
        if not datetime_str or not datetime_str.strip():
            return {"valid": False, "message": "Date/time cannot be empty"}

        # Try common datetime formats
        formats = [
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d %H:%M:%S",
            "%d/%m/%Y %H:%M",
            "%m/%d/%Y %H:%M",
            "%Y-%m-%dT%H:%M:%S",
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(datetime_str.strip(), fmt)

                # Check if datetime is in the past
                if dt < datetime.now():
                    return {"valid": False, "message": "Date/time cannot be in the past"}

                return {
                    "valid": True,
                    "message": "Valid date/time",
                    "sanitized": dt.isoformat()
                }
            except ValueError:
                continue

        return {"valid": False, "message": "Invalid date/time format. Use: YYYY-MM-DD HH:MM"}

    def sanitize_input(self, user_input: str) -> str:
        """Sanitize user input to prevent injection attacks.

        Args:
            user_input: User input to sanitize

        Returns:
            Sanitized input
        """
        if not user_input:
            return ""

        # Check for dangerous patterns
        for pattern in self.dangerous_patterns:
            if re.search(pattern, user_input, re.IGNORECASE):
                logger.warning(f"Dangerous pattern detected in input: {pattern}")
                # Remove the dangerous content
                user_input = re.sub(pattern, '', user_input, flags=re.IGNORECASE)

        # Basic sanitization
        user_input = user_input.strip()

        # Remove excessive whitespace
        user_input = re.sub(r'\s+', ' ', user_input)

        return user_input

    def validate_reservation_data(
        self,
        first_name: str,
        last_name: str,
        car_number: str,
        start_time: str,
        end_time: str
    ) -> Dict[str, Any]:
        """Validate complete reservation data.

        Args:
            first_name: User's first name
            last_name: User's last name
            car_number: Vehicle registration number
            start_time: Reservation start time
            end_time: Reservation end time

        Returns:
            Validation result with sanitized data
        """
        errors = []
        sanitized_data = {}

        # Validate first name
        first_name_result = self.validate_name(first_name)
        if not first_name_result["valid"]:
            errors.append(f"First name: {first_name_result['message']}")
        else:
            sanitized_data["first_name"] = first_name_result["sanitized"]

        # Validate last name
        last_name_result = self.validate_name(last_name)
        if not last_name_result["valid"]:
            errors.append(f"Last name: {last_name_result['message']}")
        else:
            sanitized_data["last_name"] = last_name_result["sanitized"]

        # Validate car number
        car_result = self.validate_car_number(car_number)
        if not car_result["valid"]:
            errors.append(f"Car number: {car_result['message']}")
        else:
            sanitized_data["car_number"] = car_result["sanitized"]

        # Validate start time
        start_result = self.validate_datetime(start_time)
        if not start_result["valid"]:
            errors.append(f"Start time: {start_result['message']}")
        else:
            sanitized_data["start_time"] = start_result["sanitized"]

        # Validate end time
        end_result = self.validate_datetime(end_time)
        if not end_result["valid"]:
            errors.append(f"End time: {end_result['message']}")
        else:
            sanitized_data["end_time"] = end_result["sanitized"]

        # Check if end time is after start time
        if not errors and "start_time" in sanitized_data and "end_time" in sanitized_data:
            start_dt = datetime.fromisoformat(sanitized_data["start_time"])
            end_dt = datetime.fromisoformat(sanitized_data["end_time"])

            if end_dt <= start_dt:
                errors.append("End time must be after start time")

        if errors:
            return {
                "valid": False,
                "errors": errors
            }

        return {
            "valid": True,
            "data": sanitized_data
        }
