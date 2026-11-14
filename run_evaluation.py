"""Script to run evaluation on the RAG system."""
import logging
from dotenv import load_dotenv
from src.config.settings import get_settings
from src.chatbot.chatbot import ParkingChatbot
from src.evaluation.metrics import RAGEvaluator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_evaluation():
    """Run evaluation on predefined test cases."""
    # Load environment
    load_dotenv()

    # Initialize chatbot
    logger.info("Initializing chatbot for evaluation...")
    settings = get_settings()
    chatbot = ParkingChatbot(settings)

    # Define test queries
    test_queries = [
        "What are your operating hours?",
        "How much does parking cost?",
        "Are there available spaces?",
        "Where is the parking located?",
        "Do you have EV charging stations?",
        "What is your cancellation policy?",
        "Can I extend my reservation?",
        "What payment methods do you accept?"
    ]

    logger.info(f"Running evaluation on {len(test_queries)} test queries...")

    # Run queries and collect metrics
    results = []
    for i, query in enumerate(test_queries, 1):
        logger.info(f"Processing query {i}/{len(test_queries)}: {query}")

        try:
            response = chatbot.process_message(query)
            logger.info(f"Response length: {len(response)} characters")

            # Print for manual inspection
            print(f"\n{'='*60}")
            print(f"Query {i}: {query}")
            print(f"{'='*60}")
            print(f"Response: {response[:200]}...")
            print()

        except Exception as e:
            logger.error(f"Error processing query: {e}")

    # Get statistics
    evaluator = chatbot.get_evaluator()
    stats = evaluator.get_statistics()

    if stats:
        print("\n" + evaluator.generate_report())

        # Save report to file
        with open("evaluation_report.txt", "w") as f:
            f.write(evaluator.generate_report())
        logger.info("Evaluation report saved to evaluation_report.txt")
    else:
        logger.warning("No statistics collected")

    logger.info("Evaluation complete!")


if __name__ == "__main__":
    run_evaluation()
