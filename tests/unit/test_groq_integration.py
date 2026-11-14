"""Tests for Groq API integration."""
import pytest
from unittest.mock import Mock, patch
from src.config.settings import Settings
from src.rag.generator import RAGGenerator


class TestGroqIntegration:
    """Test Groq API integration."""

    def test_settings_with_openai_only(self):
        """Test settings with only OpenAI key."""
        with patch.dict('os.environ', {
            'OPENAI_API_KEY': 'sk-test-key',
            'DATABASE_URL': 'sqlite:///test.db'
        }, clear=True):
            settings = Settings(_env_file=None)
            assert settings.get_active_provider() == "openai"
            assert settings.get_active_api_key() == "sk-test-key"

    def test_settings_with_groq_only(self):
        """Test settings with only Groq key."""
        with patch.dict('os.environ', {
            'GROQ_API_KEY': 'gsk-test-key',
            'DATABASE_URL': 'sqlite:///test.db'
        }, clear=True):
            settings = Settings(_env_file=None)
            assert settings.get_active_provider() == "groq"
            assert settings.get_active_api_key() == "gsk-test-key"

    def test_settings_with_both_keys_default_openai(self):
        """Test settings with both keys defaults to OpenAI."""
        with patch.dict('os.environ', {
            'OPENAI_API_KEY': 'sk-test-key',
            'GROQ_API_KEY': 'gsk-test-key',
            'DATABASE_URL': 'sqlite:///test.db'
        }, clear=True):
            settings = Settings(_env_file=None)
            assert settings.get_active_provider() == "openai"
            assert settings.get_active_api_key() == "sk-test-key"

    def test_settings_with_both_keys_explicit_groq(self):
        """Test settings with both keys and explicit Groq provider."""
        with patch.dict('os.environ', {
            'OPENAI_API_KEY': 'sk-test-key',
            'GROQ_API_KEY': 'gsk-test-key',
            'LLM_PROVIDER': 'groq',
            'DATABASE_URL': 'sqlite:///test.db'
        }, clear=True):
            settings = Settings(_env_file=None)
            assert settings.get_active_provider() == "groq"
            assert settings.get_active_api_key() == "gsk-test-key"

    def test_settings_with_no_keys_raises_error(self):
        """Test settings with no API keys raises ValueError."""
        with patch.dict('os.environ', {
            'DATABASE_URL': 'sqlite:///test.db'
        }, clear=True):
            settings = Settings(_env_file=None)
            with pytest.raises(ValueError, match="No LLM API key configured"):
                settings.get_active_provider()

    def test_generator_openai_initialization(self):
        """Test generator initialization with OpenAI."""
        with patch('src.rag.generator.ChatOpenAI') as mock_openai:
            generator = RAGGenerator(
                model_name="gpt-3.5-turbo",
                api_key="sk-test",
                provider="openai"
            )
            mock_openai.assert_called_once()
            assert generator.provider == "openai"

    @patch('src.rag.generator.GROQ_AVAILABLE', True)
    def test_generator_groq_initialization(self):
        """Test generator initialization with Groq."""
        with patch('src.rag.generator.ChatGroq') as mock_groq:
            generator = RAGGenerator(
                model_name="gpt-3.5-turbo",
                api_key="gsk-test",
                provider="groq"
            )
            mock_groq.assert_called_once()
            assert generator.provider == "groq"

    @patch('src.rag.generator.GROQ_AVAILABLE', True)
    def test_generator_groq_model_mapping(self):
        """Test Groq model mapping from OpenAI models."""
        # Updated to reflect current model mapping (openai/gpt-oss-20b for all models)
        test_cases = [
            ("gpt-3.5-turbo", "openai/gpt-oss-20b"),
            ("gpt-4", "openai/gpt-oss-20b"),
            ("gpt-4-turbo", "openai/gpt-oss-20b"),
        ]

        for openai_model, expected_groq_model in test_cases:
            with patch('src.rag.generator.ChatGroq') as mock_groq:
                RAGGenerator(
                    model_name=openai_model,
                    api_key="gsk-test",
                    provider="groq"
                )
                # Verify the Groq model was used
                call_kwargs = mock_groq.call_args[1]
                assert call_kwargs['model'] == expected_groq_model

    @patch('src.rag.generator.GROQ_AVAILABLE', False)
    def test_generator_groq_unavailable_raises_error(self):
        """Test generator raises error when Groq is not available."""
        with pytest.raises(ImportError, match="Groq support requires langchain-groq"):
            RAGGenerator(
                model_name="gpt-3.5-turbo",
                api_key="gsk-test",
                provider="groq"
            )

    def test_generator_invalid_provider_raises_error(self):
        """Test generator raises error for invalid provider."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            RAGGenerator(
                model_name="gpt-3.5-turbo",
                api_key="test-key",
                provider="invalid"
            )

    @patch('src.rag.generator.GROQ_AVAILABLE', True)
    def test_generator_groq_generation(self):
        """Test response generation with Groq provider."""
        with patch('src.rag.generator.ChatGroq') as mock_groq:
            # Mock the LLM chain
            mock_llm = Mock()
            mock_llm.invoke.return_value = "Test response"
            mock_groq.return_value = mock_llm

            generator = RAGGenerator(
                model_name="gpt-3.5-turbo",
                api_key="gsk-test",
                provider="groq"
            )

            # Mock the chain components
            with patch.object(generator, 'llm', mock_llm):
                context = {
                    'static_context': 'Static info',
                    'dynamic_context': 'Dynamic info'
                }

                # Note: Actual generation would need more mocking of LangChain components
                # This test verifies the generator was initialized correctly
                assert generator.provider == "groq"
                assert generator.llm == mock_llm


class TestProviderSelection:
    """Test provider selection logic."""

    def test_explicit_provider_overrides_default(self):
        """Test explicit provider setting overrides default."""
        with patch.dict('os.environ', {
            'OPENAI_API_KEY': 'sk-test',
            'GROQ_API_KEY': 'gsk-test',
            'LLM_PROVIDER': 'GROQ',  # Test case insensitivity
            'DATABASE_URL': 'sqlite:///test.db'
        }, clear=True):
            settings = Settings(_env_file=None)
            assert settings.get_active_provider() == "groq"

    def test_openai_preferred_when_both_available(self):
        """Test OpenAI is preferred when both keys available."""
        with patch.dict('os.environ', {
            'OPENAI_API_KEY': 'sk-test',
            'GROQ_API_KEY': 'gsk-test',
            'DATABASE_URL': 'sqlite:///test.db'
        }, clear=True):
            settings = Settings(_env_file=None)
            # Without explicit LLM_PROVIDER, should default to OpenAI
            assert settings.get_active_provider() == "openai"

    def test_groq_fallback_when_only_groq_available(self):
        """Test Groq is used as fallback when OpenAI not available."""
        with patch.dict('os.environ', {
            'GROQ_API_KEY': 'gsk-test',
            'DATABASE_URL': 'sqlite:///test.db'
        }, clear=True):
            settings = Settings(_env_file=None)
            assert settings.get_active_provider() == "groq"


class TestAPIKeyRetrieval:
    """Test API key retrieval logic."""

    def test_get_openai_key(self):
        """Test retrieving OpenAI API key."""
        with patch.dict('os.environ', {
            'OPENAI_API_KEY': 'sk-test-123',
            'DATABASE_URL': 'sqlite:///test.db'
        }, clear=True):
            settings = Settings(_env_file=None)
            assert settings.get_active_api_key() == "sk-test-123"

    def test_get_groq_key(self):
        """Test retrieving Groq API key."""
        with patch.dict('os.environ', {
            'GROQ_API_KEY': 'gsk-test-456',
            'DATABASE_URL': 'sqlite:///test.db'
        }, clear=True):
            settings = Settings(_env_file=None)
            assert settings.get_active_api_key() == "gsk-test-456"

    def test_get_key_with_explicit_provider(self):
        """Test key retrieval with explicit provider."""
        with patch.dict('os.environ', {
            'OPENAI_API_KEY': 'sk-test',
            'GROQ_API_KEY': 'gsk-test',
            'LLM_PROVIDER': 'groq',
            'DATABASE_URL': 'sqlite:///test.db'
        }, clear=True):
            settings = Settings(_env_file=None)
            assert settings.get_active_api_key() == "gsk-test"
