"""Sensitive data filter using Presidio for PII detection and anonymization."""
import logging
import re
from typing import List, Dict, Any, Optional
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_anonymizer import AnonymizerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider

logger = logging.getLogger(__name__)


class SensitiveDataFilter:
    """Filter for detecting and anonymizing sensitive data."""

    def __init__(self):
        """Initialize sensitive data filter with Presidio engines."""
        try:
            # Initialize NLP engine
            provider = NlpEngineProvider()
            nlp_engine = provider.create_engine()

            # Initialize analyzer and anonymizer
            self.analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
            self.anonymizer = AnonymizerEngine()

            # Add custom recognizers
            self._add_custom_recognizers()

            logger.info("Sensitive data filter initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing sensitive data filter: {e}")
            # Fallback to regex-based filtering
            self.analyzer = None
            self.anonymizer = None

    def _add_custom_recognizers(self):
        """Add custom pattern recognizers for specific data types."""
        # License plate pattern (various formats)
        license_plate_pattern = Pattern(
            name="license_plate_pattern",
            regex=r"\b[A-Z]{2,3}[-\s]?\d{2,4}[-\s]?[A-Z]{0,2}\b",
            score=0.7
        )

        license_plate_recognizer = PatternRecognizer(
            supported_entity="LICENSE_PLATE",
            patterns=[license_plate_pattern]
        )

        if self.analyzer:
            self.analyzer.registry.add_recognizer(license_plate_recognizer)

    def detect_sensitive_data(self, text: str, language: str = "en") -> List[Dict[str, Any]]:
        """Detect sensitive data in text.

        Args:
            text: Text to analyze
            language: Language code

        Returns:
            List of detected PII entities
        """
        if not self.analyzer:
            return self._fallback_detect(text)

        try:
            results = self.analyzer.analyze(
                text=text,
                language=language,
                entities=[
                    "PERSON",
                    "EMAIL_ADDRESS",
                    "PHONE_NUMBER",
                    "CREDIT_CARD",
                    "LICENSE_PLATE",
                    "IBAN_CODE",
                    "US_SSN",
                    "US_DRIVER_LICENSE"
                ]
            )

            detected = [
                {
                    "entity_type": result.entity_type,
                    "start": result.start,
                    "end": result.end,
                    "score": result.score,
                    "text": text[result.start:result.end]
                }
                for result in results
            ]

            if detected:
                logger.warning(f"Detected {len(detected)} sensitive entities in text")

            return detected

        except Exception as e:
            logger.error(f"Error detecting sensitive data: {e}")
            return self._fallback_detect(text)

    def _fallback_detect(self, text: str) -> List[Dict[str, Any]]:
        """Fallback regex-based detection."""
        detected = []

        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        for match in re.finditer(email_pattern, text):
            detected.append({
                "entity_type": "EMAIL_ADDRESS",
                "start": match.start(),
                "end": match.end(),
                "score": 0.8,
                "text": match.group()
            })

        # Phone pattern
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        for match in re.finditer(phone_pattern, text):
            detected.append({
                "entity_type": "PHONE_NUMBER",
                "start": match.start(),
                "end": match.end(),
                "score": 0.7,
                "text": match.group()
            })

        return detected

    def anonymize_text(self, text: str, language: str = "en") -> str:
        """Anonymize sensitive data in text.

        Args:
            text: Text to anonymize
            language: Language code

        Returns:
            Anonymized text
        """
        if not self.analyzer or not self.anonymizer:
            return self._fallback_anonymize(text)

        try:
            # Analyze text
            results = self.analyzer.analyze(
                text=text,
                language=language,
                entities=[
                    "PERSON",
                    "EMAIL_ADDRESS",
                    "PHONE_NUMBER",
                    "CREDIT_CARD",
                    "LICENSE_PLATE"
                ]
            )

            # Anonymize
            anonymized_result = self.anonymizer.anonymize(
                text=text,
                analyzer_results=results
            )

            return anonymized_result.text

        except Exception as e:
            logger.error(f"Error anonymizing text: {e}")
            return self._fallback_anonymize(text)

    def _fallback_anonymize(self, text: str) -> str:
        """Fallback regex-based anonymization."""
        # Anonymize emails
        text = re.sub(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            '[EMAIL]',
            text
        )

        # Anonymize phones
        text = re.sub(
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            '[PHONE]',
            text
        )

        return text

    def is_safe_to_share(self, text: str, threshold: float = 0.7) -> bool:
        """Check if text is safe to share (no high-confidence PII).

        Args:
            text: Text to check
            threshold: Confidence threshold

        Returns:
            True if safe to share, False otherwise
        """
        detected = self.detect_sensitive_data(text)

        # Check if any high-confidence PII detected
        high_confidence_pii = [
            entity for entity in detected
            if entity["score"] >= threshold
        ]

        if high_confidence_pii:
            logger.warning(f"Text contains {len(high_confidence_pii)} high-confidence PII entities")
            return False

        return True

    def filter_response(self, response: str) -> str:
        """Filter response to remove any inadvertently exposed sensitive data.

        Args:
            response: Response text to filter

        Returns:
            Filtered response
        """
        # Detect sensitive data
        detected = self.detect_sensitive_data(response)

        # If sensitive data found, anonymize
        if detected:
            logger.warning("Sensitive data detected in response, anonymizing...")
            return self.anonymize_text(response)

        return response
