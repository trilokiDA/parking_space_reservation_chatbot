# Setup Guide - Intelligent Parking Chatbot

This guide will walk you through setting up the chatbot from scratch.

## Prerequisites

- Python 3.9 or higher
- pip package manager
- **OpenAI API key** ([Get one here](https://platform.openai.com/api-keys)) 
  **OR** 
- **Groq API key** ([Get one here](https://console.groq.com)) - Faster & cheaper alternative!
- Git (optional, for version control)

> 💡 **New Feature**: You can now use either OpenAI or Groq APIs. See [GROQ_INTEGRATION.md](GROQ_INTEGRATION.md) for details.

## Step-by-Step Setup

### 1. Environment Setup

#### Option A: Using venv (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate
```

#### Option B: Using conda

```bash
# Create conda environment
conda create -n parking-chatbot python=3.10

# Activate environment
conda activate parking-chatbot
```

### 2. Install Dependencies

```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install requirements
pip install -r requirements.txt
```

**Note**: If you encounter issues installing `presidio-analyzer` or `presidio-anonymizer` on Windows:

```bash
# Install Microsoft C++ Build Tools first
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/

# Or install without presidio (with reduced PII detection)
pip install -r requirements.txt --no-deps
pip install langchain langchain-community langchain-openai langgraph
pip install faiss-cpu sentence-transformers sqlalchemy openai
pip install pandas numpy python-dotenv pytest pytest-asyncio pytest-cov
pip install scikit-learn pydantic pydantic-settings tqdm
```

### 3. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env file and add your OpenAI API key
# On Windows, you can use:
notepad .env

# On Linux/Mac:
nano .env
```

**Required variables in .env (choose one or both):**

**Option A: OpenAI Only**
```env
OPENAI_API_KEY=sk-your-actual-api-key-here
```

**Option B: Groq + OpenAI (Recommended for cost savings)**
```env
OPENAI_API_KEY=sk-your-openai-key  # For embeddings
GROQ_API_KEY=gsk-your-groq-key     # For LLM (faster!)
LLM_PROVIDER=groq
```

**Option C: Groq Only (Limited - no vector store creation)**
```env
GROQ_API_KEY=gsk-your-groq-key
```

**Optional configurations:**
```env
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-3.5-turbo
LLM_TEMPERATURE=0.7
MAX_TOKENS=500
LLM_PROVIDER=openai  # or 'groq' (auto-detected if not set)
```

### 4. Initialize the Vector Store

This step loads your static parking data into the FAISS vector database:

```bash
python init_vectorstore.py
```

**Expected output:**
```
INFO - Starting vector store initialization...
INFO - Loading documents from: data/static_data
INFO - Loaded document: parking_info.txt
INFO - Loaded document: reservation_process.txt
INFO - Loaded document: faq.txt
INFO - Loaded 3 documents
INFO - Creating vector store...
INFO - Split 3 documents into XX chunks
INFO - Vector store created successfully
INFO - Saving vector store...
INFO - Vector store initialized successfully at: vectorstore/faiss_index
```

### 5. Verify Installation

Run the test suite to ensure everything is working:

```bash
pytest tests/unit -v
```

**Expected output:**
```
tests/unit/test_database.py::TestDatabaseManager::test_initialization PASSED
tests/unit/test_database.py::TestDatabaseManager::test_get_dynamic_data PASSED
...
======================== XX passed in X.XXs ========================
```

### 6. Run the Chatbot

```bash
python main.py
```

You should see:
```
============================================================
    INTELLIGENT PARKING RESERVATION CHATBOT
============================================================

Welcome! I can help you with:
  • General parking information
  • Availability and pricing
  • Making reservations
  • Answering your questions

Type 'quit' or 'exit' to end the conversation.
Type 'help' for assistance.
============================================================

You: 
```

## Testing Your Setup

### Test 1: Information Query

```
You: What are your operating hours?
```

**Expected**: The bot should provide detailed operating hours from the knowledge base.

### Test 2: Pricing Query

```
You: How much does parking cost?
```

**Expected**: The bot should list hourly, daily, weekly, and monthly rates.

### Test 3: Reservation Flow

```
You: I want to make a reservation
```

**Expected**: The bot should start asking for your information step by step.

## Common Issues and Solutions

### Issue 1: "OPENAI_API_KEY not found"

**Solution:**
```bash
# Verify .env file exists
ls -la .env  # Linux/Mac
dir .env     # Windows

# Check file content
cat .env     # Linux/Mac
type .env    # Windows

# Ensure format is:
OPENAI_API_KEY=sk-...
# (no quotes, no spaces around =)
```

### Issue 2: "Vector store not found"

**Solution:**
```bash
# Run initialization script
python init_vectorstore.py

# Verify vector store was created
ls -la vectorstore/  # Linux/Mac
dir vectorstore\     # Windows
```

### Issue 3: Import errors

**Solution:**
```bash
# Ensure you're in the correct directory
pwd  # Should show: .../intelligent_chatbot

# Verify Python can find modules
python -c "import src.chatbot"

# If error, ensure __init__.py files exist
ls src/__init__.py
ls src/chatbot/__init__.py
```

### Issue 4: "Module 'presidio' not found"

This is common on Windows. Two options:

**Option A: Install build tools**
```bash
# Install Microsoft C++ Build Tools
# Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/

# Retry installation
pip install presidio-analyzer presidio-anonymizer
```

**Option B: Run without Presidio**

The code will automatically fall back to regex-based PII detection if Presidio is not available. The system will still work but with reduced PII detection capabilities.

### Issue 5: Database errors

**Solution:**
```bash
# Delete existing database and restart
rm data/dynamic_data.db  # Linux/Mac
del data\dynamic_data.db  # Windows

# Restart the chatbot
python main.py
```

## Performance Optimization

### Use Better Models

Edit `.env`:
```env
# For better quality (more expensive)
LLM_MODEL=gpt-4
EMBEDDING_MODEL=text-embedding-3-large

# For faster responses (cheaper)
LLM_MODEL=gpt-3.5-turbo
EMBEDDING_MODEL=text-embedding-3-small
```

### Adjust Retrieval Parameters

Edit `.env`:
```env
# Number of documents to retrieve
RETRIEVAL_K=5

# Chunk size for text splitting
CHUNK_SIZE=1000
CHUNK_OVERLAP=100
```

## Development Setup

For development work:

```bash
# Install development dependencies
pip install black flake8 mypy ipython

# Format code
black src tests

# Lint code
flake8 src tests --max-line-length=100

# Run tests with coverage
pytest --cov=src --cov-report=html

# Open coverage report
open htmlcov/index.html  # Mac
start htmlcov/index.html  # Windows
xdg-open htmlcov/index.html  # Linux
```

## Next Steps

1. **Customize Data**: Add your own parking information in `data/static_data/`
2. **Run Evaluation**: `python run_evaluation.py` to benchmark performance
3. **Review Tests**: Check `tests/unit/` for examples
4. **Read Architecture**: See `README.md` for system architecture details

## Getting Help

- Check the main `README.md` for comprehensive documentation
- Review error logs in the console output
- Enable debug logging by setting `LOG_LEVEL=DEBUG` in `.env`
- Run `python main.py` and type `help` for available commands

## Quick Reference Commands

```bash
# Setup
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API key

# Initialize
python init_vectorstore.py

# Run
python main.py

# Test
pytest

# Evaluate
python run_evaluation.py
```

---

**Setup complete!** 🎉 You're ready to use the parking chatbot.
