"""Main chatbot class for parking reservation system."""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from ..config.settings import Settings
from ..database.db_manager import DatabaseManager
from ..rag.vector_store import VectorStoreManager
from ..rag.retriever import RAGRetriever
from ..rag.generator import RAGGenerator
from ..guardrails.sensitive_data_filter import SensitiveDataFilter
from ..guardrails.input_validator import InputValidator
from ..evaluation.metrics import RAGEvaluator

logger = logging.getLogger(__name__)


class ParkingChatbot:
    """Main chatbot class for parking space reservation."""

    def __init__(self, settings: Settings):
        """Initialize parking chatbot.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.conversation_state = {}
        self.reservation_data = {}

        # Initialize components
        logger.info("Initializing chatbot components...")

        # Determine active provider
        try:
            provider = settings.get_active_provider()
            api_key = settings.get_active_api_key()
            logger.info(f"Using LLM provider: {provider}")
        except ValueError as e:
            logger.error(str(e))
            raise

        self.db_manager = DatabaseManager(settings.database_url)

        # For embeddings: use OpenAI if available, otherwise use local HuggingFace model
        embedding_api_key = settings.openai_api_key
        if not settings.openai_api_key and provider == "groq":
            logger.info(
                "Using Groq for LLM. Embeddings will use local HuggingFace model (no API key needed)."
            )
            embedding_api_key = None

        self.vector_store_manager = VectorStoreManager(
            embedding_model=settings.embedding_model,
            api_key=embedding_api_key,
            vector_store_path=settings.vector_store_path,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap
        )

        # Try to load existing vector store, create if not exists
        try:
            self.vector_store_manager.load_vector_store()
            logger.info("Loaded existing vector store")
        except Exception as e:
            logger.warning(f"Could not load vector store: {e}")
            logger.info("Vector store will be created when documents are added")

        self.retriever = RAGRetriever(
            vector_store_manager=self.vector_store_manager,
            db_manager=self.db_manager,
            retrieval_k=settings.retrieval_k
        )

        self.generator = RAGGenerator(
            model_name=settings.llm_model,
            api_key=api_key,
            temperature=settings.llm_temperature,
            max_tokens=settings.max_tokens,
            provider=provider
        )

        self.sensitive_filter = SensitiveDataFilter()
        self.input_validator = InputValidator()
        self.evaluator = RAGEvaluator()

        logger.info("Chatbot initialized successfully")

    def process_message(self, user_message: str) -> str:
        """Process user message and generate response.

        Args:
            user_message: User's message

        Returns:
            Bot's response
        """
        try:
            # Sanitize input
            sanitized_message = self.input_validator.sanitize_input(user_message)

            # Check if user is in reservation flow
            if self._is_in_reservation_flow():
                return self._handle_reservation_flow(sanitized_message)

            # Check if user wants to make a reservation
            if self._is_reservation_request(sanitized_message):
                return self._start_reservation_flow()

            # Regular information query - use RAG
            response, latency = self.evaluator.measure_latency(
                self._generate_rag_response,
                sanitized_message
            )

            # Filter response for sensitive data
            filtered_response = self.sensitive_filter.filter_response(response)

            logger.info(f"Processed message in {latency:.2f}ms")
            return filtered_response

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "I apologize, but I encountered an error. Please try again or rephrase your question."

    def _generate_rag_response(self, query: str) -> str:
        """Generate response using RAG pipeline.

        Args:
            query: User query

        Returns:
            Generated response
        """
        # Retrieve context
        context = self.retriever.retrieve(query)

        # Generate response
        response = self.generator.generate(query, context)

        return response

    def _is_reservation_request(self, message: str) -> bool:
        """Check if message is a reservation request.

        Args:
            message: User message

        Returns:
            True if reservation request, False otherwise
        """
        reservation_keywords = [
            "book", "reserve", "reservation", "make a booking",
            "i want to park", "need a spot", "need parking"
        ]

        message_lower = message.lower()
        return any(keyword in message_lower for keyword in reservation_keywords)

    def _start_reservation_flow(self) -> str:
        """Start reservation collection flow.

        Returns:
            Initial prompt for user
        """
        self.conversation_state = {"flow": "reservation", "step": "first_name"}
        self.reservation_data = {}

        return ("I'd be happy to help you make a reservation! "
                "Let's collect some information.\n\n"
                "First, what is your first name?")

    def _is_in_reservation_flow(self) -> bool:
        """Check if user is in reservation flow.

        Returns:
            True if in reservation flow, False otherwise
        """
        return self.conversation_state.get("flow") == "reservation"

    def _handle_reservation_flow(self, user_input: str) -> str:
        """Handle reservation data collection flow.

        Args:
            user_input: User's input

        Returns:
            Next prompt or confirmation message
        """
        current_step = self.conversation_state.get("step")

        if current_step == "first_name":
            validation = self.input_validator.validate_name(user_input)
            if not validation["valid"]:
                return f"{validation['message']}. Please provide your first name again."

            self.reservation_data["first_name"] = validation["sanitized"]
            self.conversation_state["step"] = "last_name"
            return "Great! What is your last name?"

        elif current_step == "last_name":
            validation = self.input_validator.validate_name(user_input)
            if not validation["valid"]:
                return f"{validation['message']}. Please provide your last name again."

            self.reservation_data["last_name"] = validation["sanitized"]
            self.conversation_state["step"] = "car_number"
            return "Thank you! What is your car registration number?"

        elif current_step == "car_number":
            validation = self.input_validator.validate_car_number(user_input)
            if not validation["valid"]:
                return f"{validation['message']}. Please provide your car number again."

            self.reservation_data["car_number"] = validation["sanitized"]
            self.conversation_state["step"] = "start_time"
            return ("Perfect! When would you like to start your parking? "
                    "Please use format: YYYY-MM-DD HH:MM (e.g., 2024-12-25 14:30)")

        elif current_step == "start_time":
            validation = self.input_validator.validate_datetime(user_input)
            if not validation["valid"]:
                return f"{validation['message']}. Please provide the start time again."

            self.reservation_data["start_time"] = validation["sanitized"]
            self.conversation_state["step"] = "end_time"
            return "And when would you like to end your parking? (Same format: YYYY-MM-DD HH:MM)"

        elif current_step == "end_time":
            validation = self.input_validator.validate_datetime(user_input)
            if not validation["valid"]:
                return f"{validation['message']}. Please provide the end time again."

            self.reservation_data["end_time"] = validation["sanitized"]

            # Validate complete reservation data
            complete_validation = self.input_validator.validate_reservation_data(
                first_name=self.reservation_data["first_name"],
                last_name=self.reservation_data["last_name"],
                car_number=self.reservation_data["car_number"],
                start_time=self.reservation_data["start_time"],
                end_time=self.reservation_data["end_time"]
            )

            if not complete_validation["valid"]:
                errors = "\n".join(complete_validation["errors"])
                self._reset_reservation_flow()
                return f"There were some issues with your reservation:\n{errors}\n\nPlease start over."

            # Create reservation
            return self._create_reservation(complete_validation["data"])

        return "I'm not sure what you meant. Could you please repeat that?"

    def _create_reservation(self, reservation_data: Dict[str, Any]) -> str:
        """Create reservation in database.

        Args:
            reservation_data: Validated reservation data

        Returns:
            Confirmation message
        """
        try:
            # Convert ISO format strings to datetime objects
            reservation_data_db = {
                "first_name": reservation_data["first_name"],
                "last_name": reservation_data["last_name"],
                "car_number": reservation_data["car_number"],
                "start_time": datetime.fromisoformat(reservation_data["start_time"]),
                "end_time": datetime.fromisoformat(reservation_data["end_time"]),
                "status": "pending"
            }

            reservation_id = self.db_manager.create_reservation(reservation_data_db)

            if reservation_id:
                self._reset_reservation_flow()
                return (f"✓ Reservation created successfully!\n\n"
                        f"Reservation ID: {reservation_id}\n"
                        f"Name: {reservation_data['first_name']} {reservation_data['last_name']}\n"
                        f"Car: {reservation_data['car_number']}\n"
                        f"Start: {reservation_data['start_time']}\n"
                        f"End: {reservation_data['end_time']}\n\n"
                        f"Status: Pending admin confirmation\n"
                        f"You will be notified once an administrator confirms your reservation.")
            else:
                self._reset_reservation_flow()
                return "I apologize, but there was an error creating your reservation. Please try again later."

        except Exception as e:
            logger.error(f"Error creating reservation: {e}")
            self._reset_reservation_flow()
            return "I apologize, but there was an error creating your reservation. Please try again later."

    def _reset_reservation_flow(self):
        """Reset reservation flow state."""
        self.conversation_state = {}
        self.reservation_data = {}

    def get_evaluator(self) -> RAGEvaluator:
        """Get evaluator instance for metrics.

        Returns:
            RAG evaluator instance
        """
        return self.evaluator
