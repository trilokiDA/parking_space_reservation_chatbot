"""Vector store manager for static data storage and retrieval."""
import os
import logging
from pathlib import Path
from typing import List, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """Manager for FAISS vector store operations."""

    def __init__(
        self,
        embedding_model: str,
        api_key: Optional[str],
        vector_store_path: str,
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ):
        """Initialize vector store manager.

        Args:
            embedding_model: Name of the embedding model
            api_key: OpenAI API key (optional, if None uses HuggingFace)
            vector_store_path: Path to store FAISS index
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
        """
        self.embedding_model = embedding_model

        # Use HuggingFace embeddings if no OpenAI API key provided
        if api_key:
            self.embeddings = OpenAIEmbeddings(
                model=embedding_model,
                openai_api_key=api_key
            )
            logger.info(f"Using OpenAI embeddings: {embedding_model}")
        else:
            # Use a lightweight sentence-transformers model
            model_name = "all-MiniLM-L6-v2"
            self.embeddings = HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs={'device': 'cpu'}
            )
            logger.info(f"Using HuggingFace embeddings: {model_name}")
        self.vector_store_path = vector_store_path
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.vector_store: Optional[FAISS] = None

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )

    def create_vector_store(self, documents: List[Document]) -> FAISS:
        """Create vector store from documents.

        Args:
            documents: List of documents to index

        Returns:
            FAISS vector store instance
        """
        try:
            # Split documents into chunks
            splits = self.text_splitter.split_documents(documents)
            logger.info(f"Split {len(documents)} documents into {len(splits)} chunks")

            # Create vector store
            self.vector_store = FAISS.from_documents(splits, self.embeddings)
            logger.info("Vector store created successfully")

            return self.vector_store
        except Exception as e:
            logger.error(f"Error creating vector store: {e}")
            raise

    def save_vector_store(self):
        """Save vector store to disk."""
        if self.vector_store is None:
            raise ValueError("Vector store not initialized")

        try:
            os.makedirs(os.path.dirname(self.vector_store_path), exist_ok=True)
            self.vector_store.save_local(self.vector_store_path)
            logger.info(f"Vector store saved to {self.vector_store_path}")
        except Exception as e:
            logger.error(f"Error saving vector store: {e}")
            raise

    def load_vector_store(self) -> FAISS:
        """Load vector store from disk.

        Returns:
            FAISS vector store instance
        """
        try:
            self.vector_store = FAISS.load_local(
                self.vector_store_path,
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            logger.info(f"Vector store loaded from {self.vector_store_path}")
            return self.vector_store
        except Exception as e:
            logger.error(f"Error loading vector store: {e}")
            raise

    def add_documents(self, documents: List[Document]):
        """Add new documents to existing vector store.

        Args:
            documents: List of documents to add
        """
        if self.vector_store is None:
            raise ValueError("Vector store not initialized")

        try:
            splits = self.text_splitter.split_documents(documents)
            self.vector_store.add_documents(splits)
            logger.info(f"Added {len(splits)} chunks to vector store")
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise

    def similarity_search(self, query: str, k: int = 3) -> List[Document]:
        """Perform similarity search in vector store.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List of relevant documents
        """
        if self.vector_store is None:
            raise ValueError("Vector store not initialized")

        try:
            results = self.vector_store.similarity_search(query, k=k)
            logger.debug(f"Found {len(results)} results for query: {query}")
            return results
        except Exception as e:
            logger.error(f"Error in similarity search: {e}")
            raise
