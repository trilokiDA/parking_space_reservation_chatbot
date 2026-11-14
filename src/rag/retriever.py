"""RAG retriever for combining static and dynamic data."""
import logging
from typing import List, Dict, Any
from langchain.schema import Document
from ..database.db_manager import DatabaseManager
from .vector_store import VectorStoreManager

logger = logging.getLogger(__name__)


class RAGRetriever:
    """Retriever combining vector store and database queries."""

    def __init__(
        self,
        vector_store_manager: VectorStoreManager,
        db_manager: DatabaseManager,
        retrieval_k: int = 3
    ):
        """Initialize RAG retriever.

        Args:
            vector_store_manager: Vector store manager instance
            db_manager: Database manager instance
            retrieval_k: Number of documents to retrieve
        """
        self.vector_store_manager = vector_store_manager
        self.db_manager = db_manager
        self.retrieval_k = retrieval_k

    def retrieve(self, query: str) -> Dict[str, Any]:
        """Retrieve relevant information for a query.

        Args:
            query: User query

        Returns:
            Dictionary containing static and dynamic context
        """
        try:
            # Retrieve static data from vector store
            static_docs = self.vector_store_manager.similarity_search(
                query,
                k=self.retrieval_k
            )

            # Retrieve dynamic data from database
            dynamic_data = self._retrieve_dynamic_data(query)

            # Combine context
            context = {
                "static_context": self._format_static_context(static_docs),
                "dynamic_context": self._format_dynamic_context(dynamic_data),
                "raw_static_docs": static_docs,
                "raw_dynamic_data": dynamic_data
            }

            logger.debug(f"Retrieved context for query: {query}")
            return context

        except Exception as e:
            logger.error(f"Error retrieving context: {e}")
            raise

    def _retrieve_dynamic_data(self, query: str) -> Dict[str, List[Dict[str, Any]]]:
        """Retrieve relevant dynamic data based on query.

        Args:
            query: User query

        Returns:
            Dictionary of dynamic data by type
        """
        query_lower = query.lower()
        dynamic_data = {
            "availability": [],
            "hours": [],
            "prices": []
        }

        # Determine which dynamic data to retrieve based on query keywords
        if any(keyword in query_lower for keyword in ["available", "space", "spot", "full", "empty"]):
            dynamic_data["availability"] = self.db_manager.get_dynamic_data("availability")

        if any(keyword in query_lower for keyword in ["hour", "time", "open", "close", "when"]):
            dynamic_data["hours"] = self.db_manager.get_dynamic_data("hours")

        if any(keyword in query_lower for keyword in ["price", "cost", "rate", "fee", "much"]):
            dynamic_data["prices"] = self.db_manager.get_dynamic_data("price")

        # If no specific keywords, retrieve all dynamic data
        if not any(dynamic_data.values()):
            all_data = self.db_manager.get_dynamic_data()
            for item in all_data:
                data_type = item["type"]
                if data_type in dynamic_data:
                    dynamic_data[data_type].append(item)

        return dynamic_data

    def _format_static_context(self, documents: List[Document]) -> str:
        """Format static documents into context string.

        Args:
            documents: List of retrieved documents

        Returns:
            Formatted context string
        """
        if not documents:
            return "No relevant static information found."

        context_parts = []
        for i, doc in enumerate(documents, 1):
            context_parts.append(f"[Source {i}]\n{doc.page_content}")

        return "\n\n".join(context_parts)

    def _format_dynamic_context(self, dynamic_data: Dict[str, List[Dict[str, Any]]]) -> str:
        """Format dynamic data into context string.

        Args:
            dynamic_data: Dictionary of dynamic data

        Returns:
            Formatted context string
        """
        context_parts = []

        if dynamic_data.get("availability"):
            avail_info = []
            for item in dynamic_data["availability"]:
                avail_info.append(f"{item['key'].replace('_', ' ').title()}: {item['value']}")
            if avail_info:
                context_parts.append("Current Availability:\n" + "\n".join(avail_info))

        if dynamic_data.get("hours"):
            hours_info = []
            for item in dynamic_data["hours"]:
                hours_info.append(f"{item['key'].replace('_', ' ').title()}: {item['value']}")
            if hours_info:
                context_parts.append("Working Hours:\n" + "\n".join(hours_info))

        if dynamic_data.get("prices"):
            price_info = []
            for item in dynamic_data["prices"]:
                price_info.append(f"{item['key'].replace('_', ' ').title()}: ${item['value']}")
            if price_info:
                context_parts.append("Pricing:\n" + "\n".join(price_info))

        return "\n\n".join(context_parts) if context_parts else "No relevant dynamic information found."
