"""Initialize vector store with static parking data."""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.documents import Document
from src.config.settings import get_settings
from src.rag.vector_store import VectorStoreManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_documents_from_directory(directory: Path) -> list[Document]:
    """Load documents from directory.

    Args:
        directory: Path to directory containing text files

    Returns:
        List of Document objects
    """
    documents = []

    if not directory.exists():
        logger.warning(f"Directory {directory} does not exist")
        return documents

    for file_path in directory.glob("*.txt"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

                doc = Document(
                    page_content=content,
                    metadata={
                        "source": str(file_path.name),
                        "type": "static_parking_info"
                    }
                )
                documents.append(doc)
                logger.info(f"Loaded document: {file_path.name}")
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")

    return documents


def main():
    """Initialize vector store with static data."""
    # Load environment variables
    load_dotenv()

    # Get settings
    settings = get_settings()

    logger.info("Starting vector store initialization...")

    # Initialize vector store manager
    vector_store_manager = VectorStoreManager(
        embedding_model=settings.embedding_model,
        api_key=settings.openai_api_key,
        vector_store_path=settings.vector_store_path,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap
    )

    # Load documents
    static_data_dir = settings.static_data_dir
    logger.info(f"Loading documents from: {static_data_dir}")

    documents = load_documents_from_directory(static_data_dir)

    if not documents:
        logger.error("No documents found! Please add .txt files to data/static_data/")
        return

    logger.info(f"Loaded {len(documents)} documents")

    # Create vector store
    logger.info("Creating vector store...")
    vector_store_manager.create_vector_store(documents)

    # Save vector store
    logger.info("Saving vector store...")
    vector_store_manager.save_vector_store()

    logger.info(f"Vector store initialized successfully at: {settings.vector_store_path}")
    logger.info("You can now run the chatbot with: python main.py")


if __name__ == "__main__":
    main()
