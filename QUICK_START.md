# Quick Start Guide

## Prerequisites
- Python 3.9+
- OpenAI API key

## Installation (5 minutes)

```bash
# 1. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure API key
cp .env.example .env
# Edit .env and add: OPENAI_API_KEY=your-key-here

# 4. Initialize vector store
python init_vectorstore.py

# 5. Run chatbot
python main.py
```

## Usage

**Information queries:**
- "What are your hours?"
- "How much does parking cost?"
- "Are spaces available?"

**Make reservation:**
- "I want to book a spot"
- Follow the prompts for name, car number, dates

**Commands:**
- `help` - Show help
- `stats` - View performance metrics
- `quit` - Exit

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html
```

## Troubleshooting

**No API key error:**
```bash
# Check .env file exists and contains:
OPENAI_API_KEY=sk-...
```

**Vector store error:**
```bash
# Re-initialize
python init_vectorstore.py
```

**Import errors:**
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

## Documentation

- **README.md** - Full documentation
- **SETUP_GUIDE.md** - Detailed setup
- **PROJECT_SUMMARY.md** - Complete overview
- **EVALUATION_METHODOLOGY.md** - Metrics details

## Support

See `SETUP_GUIDE.md` for detailed troubleshooting and common issues.
