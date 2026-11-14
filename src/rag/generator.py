"""RAG generator for generating responses using LLM."""
import logging
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema import StrOutputParser

try:
    from langchain_groq import ChatGroq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

logger = logging.getLogger(__name__)


class RAGGenerator:
    """Generator for creating responses using retrieved context."""

    def __init__(
        self,
        model_name: str,
        api_key: str,
        temperature: float = 0.7,
        max_tokens: int = 500,
        provider: str = "openai"
    ):
        """Initialize RAG generator.

        Args:
            model_name: Name of the LLM model
            api_key: API key for the provider
            temperature: Generation temperature
            max_tokens: Maximum tokens in response
            provider: LLM provider ('openai' or 'groq')
        """
        self.provider = provider.lower()
        self.model_name = model_name

        if self.provider == "openai":
            self.llm = ChatOpenAI(
                model=model_name,
                openai_api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens
            )
            logger.info(f"Initialized RAG generator with OpenAI model: {model_name}")
        elif self.provider == "groq":
            if not GROQ_AVAILABLE:
                raise ImportError(
                    "Groq support requires langchain-groq. Install it with: pip install langchain-groq"
                )
            # Map common OpenAI models to Groq equivalents
            groq_model_map = {
                "gpt-3.5-turbo": "llama3-8b-8192",
                "gpt-4": "llama3-70b-8192",
                "gpt-4-turbo": "mixtral-8x7b-32768"
            }
            groq_model = groq_model_map.get(model_name, "llama3-8b-8192")

            self.llm = ChatGroq(
                model=groq_model,
                groq_api_key=api_key,
                temperature=temperature,
                max_tokens=max_tokens
            )
            logger.info(f"Initialized RAG generator with Groq model: {groq_model} (mapped from {model_name})")
        else:
            raise ValueError(f"Unsupported provider: {provider}. Use 'openai' or 'groq'.")

        self.system_prompt = """You are a helpful parking reservation assistant. Your role is to:
1. Provide accurate information about the parking facility
2. Help users make reservations
3. Answer questions clearly and concisely
4. Be friendly and professional

Use the provided context to answer user questions. If the information is not in the context, politely say so.
Do not make up information or share sensitive data about other users.

Context:
{context}

User Question: {question}

Assistant Response:"""

        self.prompt_template = ChatPromptTemplate.from_template(self.system_prompt)

    def generate(
        self,
        query: str,
        context: Dict[str, Any],
        conversation_history: Optional[list] = None
    ) -> str:
        """Generate response for user query.

        Args:
            query: User query
            context: Retrieved context (static and dynamic)
            conversation_history: Optional conversation history

        Returns:
            Generated response
        """
        try:
            # Combine static and dynamic context
            full_context = f"{context['static_context']}\n\n{context['dynamic_context']}"

            # Create chain
            chain = (
                {"context": lambda x: full_context, "question": RunnablePassthrough()}
                | self.prompt_template
                | self.llm
                | StrOutputParser()
            )

            # Generate response
            response = chain.invoke(query)
            logger.debug(f"Generated response for query: {query}")

            return response

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I apologize, but I encountered an error processing your request. Please try again."

    def generate_with_custom_prompt(
        self,
        query: str,
        custom_prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate response with custom prompt.

        Args:
            query: User query
            custom_prompt: Custom prompt template
            context: Optional context

        Returns:
            Generated response
        """
        try:
            prompt = ChatPromptTemplate.from_template(custom_prompt)
            chain = prompt | self.llm | StrOutputParser()

            if context:
                response = chain.invoke({"context": context, "question": query})
            else:
                response = chain.invoke({"question": query})

            return response

        except Exception as e:
            logger.error(f"Error generating custom response: {e}")
            return "I apologize, but I encountered an error processing your request."
