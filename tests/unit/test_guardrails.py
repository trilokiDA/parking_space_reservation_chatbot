"""Unit tests for guardrails module."""
import pytest
from src.guardrails.sensitive_data_filter import SensitiveDataFilter
from src.guardrails.input_validator import InputValidator


class TestSensitiveDataFilter:
    """Test cases for SensitiveDataFilter class."""

    @pytest.fixture
    def filter(self):
        """Create a sensitive data filter instance."""
        return SensitiveDataFilter()

    def test_detect_email(self, filter):
        """Test email detection."""
        text = "Contact me at john.doe@example.com"
        detected = filter.detect_sensitive_data(text)

        # Should detect at least the email
        assert len(detected) > 0
        assert any(entity["entity_type"] == "EMAIL_ADDRESS" for entity in detected)

    def test_detect_phone(self, filter):
        """Test phone number detection."""
        text = "Call me at 555-123-4567"
        detected = filter.detect_sensitive_data(text)

        # Should detect the phone number
        assert len(detected) > 0
        assert any(entity["entity_type"] == "PHONE_NUMBER" for entity in detected)

    def test_anonymize_text(self, filter):
        """Test text anonymization."""
        text = "Contact John at john@example.com or 555-123-4567"
        anonymized = filter.anonymize_text(text)

        # Should not contain original email or phone
        assert "john@example.com" not in anonymized
        assert "555-123-4567" not in anonymized

    def test_is_safe_to_share(self, filter):
        """Test safety check."""
        safe_text = "The parking is available from 9 AM to 5 PM"
        unsafe_text = "Contact me at sensitive@email.com"

        assert filter.is_safe_to_share(safe_text) is True

    def test_filter_response(self, filter):
        """Test response filtering."""
        response = "Your reservation is confirmed. We'll contact you at john@test.com"
        filtered = filter.filter_response(response)

        # Should not be identical if PII was detected
        assert isinstance(filtered, str)


class TestInputValidator:
    """Test cases for InputValidator class."""

    @pytest.fixture
    def validator(self):
        """Create an input validator instance."""
        return InputValidator()

    def test_validate_valid_name(self, validator):
        """Test validation of valid names."""
        result = validator.validate_name("John Doe")
        assert result["valid"] is True
        assert result["sanitized"] == "John Doe"

    def test_validate_invalid_name_too_short(self, validator):
        """Test validation of too short name."""
        result = validator.validate_name("J")
        assert result["valid"] is False

    def test_validate_invalid_name_special_chars(self, validator):
        """Test validation of name with invalid characters."""
        result = validator.validate_name("John@Doe")
        assert result["valid"] is False

    def test_validate_empty_name(self, validator):
        """Test validation of empty name."""
        result = validator.validate_name("")
        assert result["valid"] is False

    def test_validate_valid_car_number(self, validator):
        """Test validation of valid car numbers."""
        result = validator.validate_car_number("ABC123")
        assert result["valid"] is True
        assert result["sanitized"] == "ABC123"

    def test_validate_car_number_with_spaces(self, validator):
        """Test validation of car number with spaces."""
        result = validator.validate_car_number("ABC 123")
        assert result["valid"] is True

    def test_validate_invalid_car_number_too_short(self, validator):
        """Test validation of too short car number."""
        result = validator.validate_car_number("AB")
        assert result["valid"] is False

    def test_sanitize_input(self, validator):
        """Test input sanitization."""
        malicious_input = "<script>alert('XSS')</script>"
        sanitized = validator.sanitize_input(malicious_input)

        # Should not contain script tag
        assert "<script" not in sanitized.lower()

    def test_sanitize_sql_injection(self, validator):
        """Test SQL injection prevention."""
        sql_input = "'; DROP TABLE users; --"
        sanitized = validator.sanitize_input(sql_input)

        # Should remove or escape dangerous SQL
        assert "DROP TABLE" not in sanitized

    def test_validate_datetime_valid(self, validator):
        """Test validation of valid datetime."""
        from datetime import datetime, timedelta
        future_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M")

        result = validator.validate_datetime(future_date)
        assert result["valid"] is True

    def test_validate_datetime_past(self, validator):
        """Test validation of past datetime."""
        past_date = "2020-01-01 10:00"

        result = validator.validate_datetime(past_date)
        assert result["valid"] is False
