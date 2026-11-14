# Intelligent Parking Reservation Chatbot - Stage 1

[![CI/CD Pipeline](https://github.com/yourusername/intelligent-chatbot/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/intelligent-chatbot/actions)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An intelligent chatbot system for parking space reservation using Retrieval-Augmented Generation (RAG) architecture with LangChain and LangGraph. This Stage 1 implementation includes core RAG functionality, guard rails for data protection, and comprehensive evaluation metrics.

## 🎯 Features

### Core Functionality
- **RAG-based Information Retrieval**: Combines vector database (FAISS) for static data and SQL database for dynamic data
- **Interactive Reservation System**: Step-by-step collection of user information (name, car number, reservation period)
- **Guard Rails Mechanism**: Presidio-based sensitive data detection and anonymization
- **Performance Evaluation**: Comprehensive metrics including latency, Recall@K, Precision@K, and MRR

### Technical Highlights
- **Flexible LLM Support**: 
  - OpenAI (GPT-3.5-turbo, GPT-4)
  - Groq (Llama 3 8B/70B, Mixtral) - **NEW!** ⚡ Up to 5x faster inference
  - Automatic provider detection and fallback
- **Hybrid Data Architecture**: 
  - Static data (general info, location, policies) → FAISS vector store
  - Dynamic data (availability, prices, hours) → SQLite database
- **Security Features**:
  - PII detection and anonymization
  - Input validation and sanitization
  - SQL injection and XSS prevention
- **Production-Ready**:
  - Comprehensive unit tests (pytest)
  - CI/CD pipeline (GitHub Actions)
  - Detailed logging and error handling
  - Performance monitoring

## 📋 Requirements

- Python 3.9 or higher
- OpenAI API key **OR** Groq API key (see [Groq Integration Guide](GROQ_INTEGRATION.md))
- Virtual environment (recommended)

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/intelligent-chatbot.git
cd intelligent-chatbot
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your API key(s):

**Option A: OpenAI (Default)**
```env
OPENAI_API_KEY=your_openai_api_key_here
```

**Option B: Groq (Alternative LLM Provider)**
```env
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_api_key_here  # Still needed for embeddings
LLM_PROVIDER=groq
```

**Option C: Groq Only (Limited Functionality)**
```env
GROQ_API_KEY=your_groq_api_key_here
```

> 📘 **New!** Groq API support for faster, cost-effective LLM inference. See [GROQ_INTEGRATION.md](GROQ_INTEGRATION.md) for details.

### 5. Initialize Vector Store

Load static data into the FAISS vector store:

```bash
python init_vectorstore.py
```

This will:
- Load all `.txt` files from `data/static_data/`
- Create embeddings using OpenAI
- Build and save the FAISS index

## 📖 Usage

### Run the Chatbot

```bash
python main.py
```

### Example Interactions

**Information Query:**
```
You: What are your operating hours?
Bot: Our facility operates 24/7, allowing you to park and retrieve your vehicle at any time...
```

**Make a Reservation:**
```
You: I want to make a reservation
Bot: I'd be happy to help you make a reservation! Let's collect some information.
     First, what is your first name?

You: John
Bot: Great! What is your last name?

You: Doe
Bot: Thank you! What is your car registration number?

You: ABC123
Bot: Perfect! When would you like to start your parking?
     Please use format: YYYY-MM-DD HH:MM

You: 2024-12-25 14:00
Bot: And when would you like to end your parking?

You: 2024-12-25 18:00
Bot: ✓ Reservation created successfully!
     Reservation ID: 1
     Status: Pending admin confirmation
```

### Available Commands

- `help` - Show available commands and examples
- `stats` - Display performance statistics
- `quit` / `exit` - Exit the chatbot

## 🧪 Testing

### Run All Tests

```bash
pytest
```

### Run Specific Test Modules

```bash
# Database tests
pytest tests/unit/test_database.py -v

# Guardrails tests
pytest tests/unit/test_guardrails.py -v

# Evaluation tests
pytest tests/unit/test_evaluation.py -v
```

### Run Tests with Coverage

```bash
pytest --cov=src --cov-report=html --cov-report=term
```

View coverage report:
```bash
# Open htmlcov/index.html in your browser
```

## 📁 Project Structure

```
intelligent_chatbot/
├── .github/
│   └── workflows/
│       └── ci.yml              # CI/CD pipeline configuration
├── data/
│   └── static_data/            # Static parking information
│       ├── parking_info.txt
│       ├── reservation_process.txt
│       └── faq.txt
├── src/
│   ├── chatbot/               # Main chatbot logic
│   │   ├── __init__.py
│   │   └── chatbot.py
│   ├── config/                # Configuration management
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── database/              # Database models and manager
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── db_manager.py
│   ├── evaluation/            # Evaluation metrics
│   │   ├── __init__.py
│   │   └── metrics.py
│   ├── guardrails/            # Security and validation
│   │   ├── __init__.py
│   │   ├── sensitive_data_filter.py
│   │   └── input_validator.py
│   └── rag/                   # RAG components
│       ├── __init__.py
│       ├── vector_store.py
│       ├── retriever.py
│       └── generator.py
├── tests/
│   └── unit/                  # Unit tests
│       ├── test_database.py
│       ├── test_evaluation.py
│       └── test_guardrails.py
├── .env.example               # Environment variables template
├── .gitignore
├── init_vectorstore.py        # Vector store initialization script
├── main.py                    # Main entry point
├── pytest.ini                 # Pytest configuration
├── requirements.txt           # Python dependencies
└── README.md
```

## 🏗️ Architecture

### RAG Pipeline

```
User Query
    ↓
Input Validation & Sanitization
    ↓
Query Classification
    ├─→ Information Query
    │       ↓
    │   Context Retrieval
    │   ├─→ Static Data (FAISS Vector Store)
    │   └─→ Dynamic Data (SQL Database)
    │       ↓
    │   Context Combination
    │       ↓
    │   LLM Response Generation
    │       ↓
    │   Sensitive Data Filtering
    │
    └─→ Reservation Request
            ↓
        Conversation State Management
            ↓
        Step-by-step Data Collection
            ↓
        Validation & Database Storage
```

### Data Flow

1. **Static Data**: Stored in FAISS vector store
   - General parking information
   - Policies and procedures
   - FAQ content

2. **Dynamic Data**: Stored in SQL database
   - Real-time availability
   - Current pricing
   - Operating hours
   - Reservation records

3. **Guard Rails**: Applied at multiple stages
   - Input sanitization (XSS, SQL injection prevention)
   - Output filtering (PII detection and anonymization)
   - Validation (format checking, business rules)

## 📊 Evaluation Metrics

The system tracks the following metrics:

- **Latency**: Response time in milliseconds
- **Recall@K**: Proportion of relevant documents retrieved in top K results
- **Precision@K**: Proportion of retrieved documents that are relevant
- **MRR (Mean Reciprocal Rank)**: Average of reciprocal ranks of first relevant result

View statistics during a session:
```
You: stats
```

## 🔒 Security Features

### Guard Rails Implementation

1. **Input Validation**
   - Name validation (2-50 characters, letters only)
   - Car number validation (3-15 characters, alphanumeric)
   - DateTime validation (future dates only)
   - XSS and SQL injection prevention

2. **Sensitive Data Protection**
   - PII detection using Presidio
   - Automatic anonymization of:
     - Email addresses
     - Phone numbers
     - Credit card numbers
     - License plates
   - Response filtering before output

3. **Database Security**
   - Parameterized queries (SQLAlchemy ORM)
   - Input sanitization
   - Type validation

## 🎯 Performance Optimization

- **Caching**: Vector embeddings are cached locally
- **Batch Processing**: Efficient document chunking
- **Lazy Loading**: Components initialized on demand
- **Connection Pooling**: Database connections managed efficiently

## 🔧 Configuration

### Environment Variables

See `.env.example` for all available configuration options:

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `EMBEDDING_MODEL`: Embedding model to use (default: text-embedding-3-small)
- `LLM_MODEL`: LLM model for generation (default: gpt-3.5-turbo)
- `LLM_TEMPERATURE`: Generation temperature (default: 0.7)
- `DATABASE_URL`: Database connection string
- `VECTOR_STORE_PATH`: Path to FAISS index
- `LOG_LEVEL`: Logging level (default: INFO)

### Customization

1. **Add Static Data**: Place `.txt` files in `data/static_data/` and re-run `init_vectorstore.py`
2. **Modify Dynamic Data**: Edit initial data in `src/database/db_manager.py`
3. **Adjust Guard Rails**: Configure thresholds in `src/guardrails/sensitive_data_filter.py`
4. **Change Prompts**: Modify system prompts in `src/rag/generator.py`

## 🐛 Troubleshooting

### Common Issues

**Issue**: `OPENAI_API_KEY not found`
```bash
# Solution: Ensure .env file exists with your API key
cp .env.example .env
# Edit .env and add your key
```

**Issue**: `Vector store not found`
```bash
# Solution: Initialize the vector store
python init_vectorstore.py
```

**Issue**: `Module not found errors`
```bash
# Solution: Reinstall dependencies
pip install -r requirements.txt
```

**Issue**: Presidio installation fails on Windows
```bash
# Solution: Install build tools
pip install --upgrade setuptools wheel
# Then retry: pip install -r requirements.txt
```

## 📈 Future Enhancements (Stages 2-4)

- [ ] LangGraph-based conversation flow management
- [ ] Human-in-the-loop admin approval workflow
- [ ] Multi-turn conversation with context retention
- [ ] Advanced reservation conflict detection
- [ ] Email/SMS notifications
- [ ] Web-based interface
- [ ] Multi-language support

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📧 Contact

Project Link: [https://github.com/yourusername/intelligent-chatbot](https://github.com/yourusername/intelligent-chatbot)

## 🙏 Acknowledgments

- [LangChain](https://langchain.com/) - RAG framework
- [OpenAI](https://openai.com/) - LLM and embeddings
- [FAISS](https://github.com/facebookresearch/faiss) - Vector similarity search
- [Presidio](https://microsoft.github.io/presidio/) - PII detection and anonymization
- [SQLAlchemy](https://www.sqlalchemy.org/) - Database ORM

---

**Stage 1 Complete** ✅ - Basic RAG system with guard rails and evaluation metrics implemented.
