# Quick Start Guide - Stage 4: LangGraph Orchestration

## 🚀 5-Minute Setup

### Step 1: Verify Prerequisites
```bash
# Ensure Stages 1-3 are working
python -c "from src.chatbot.chatbot import ParkingChatbot; print('✓ Stage 1 OK')"
python -c "from src.admin_agent.admin_agent_db import AdminAgentDB; print('✓ Stage 2 OK')"
python -c "from src.mcp_server.mcp_server import app; print('✓ Stage 3 OK')"
```

### Step 2: Install LangGraph (if not already installed)
```bash
pip install langgraph langchain-core
```

### Step 3: Run the Orchestrated System
```bash
python orchestrated_main.py
```

That's it! You're now running the complete orchestrated system.

## 💬 Example Interaction

```
🗣️  You: What are your operating hours?
🤖 Bot: Our parking facility operates 24/7...
💬 Workflow Stage: User Interaction

🗣️  You: I want to make a reservation
🤖 Bot: I'd be happy to help! What is your first name?
[... collect information ...]
🤖 Bot: ✓ Reservation created! ID: 15
⏳ Workflow Stage: Awaiting Approval

🗣️  You: Check status of reservation 15
🤖 Bot: Reservation #15 Status: Approved
✅ Workflow Stage: Completed
```

## 🧪 Run Tests

```bash
# Unit tests
pytest tests/unit/test_orchestration.py -v

# Integration tests
pytest tests/integration/test_full_workflow.py -v

# All Stage 4 tests
pytest tests/unit/test_orchestration.py tests/integration/test_full_workflow.py -v
```

## 🎬 Run Demo

```bash
python demo_stage4.py
```

This interactive demo walks you through all Stage 4 features!

## 📖 Full Documentation

See [STAGE4_README.md](STAGE4_README.md) for complete documentation.

## ❓ Troubleshooting

**Issue**: Import errors
```bash
# Solution: Reinstall dependencies
pip install -r requirements.txt
```

**Issue**: Database errors
```bash
# Solution: Reinitialize vector store
python init_vectorstore.py
```

## 🎯 Key Commands

| Command | Description |
|---------|-------------|
| `help` | Show available commands |
| `workflow` | Display workflow architecture |
| `stats` | Show performance statistics |
| `quit` | Exit the application |

## 🔗 Links

- [Main README](README.md)
- [Stage 4 Full Documentation](STAGE4_README.md)
- [Stage 4 Implementation Summary](STAGE4_IMPLEMENTATION_SUMMARY.md)
- [GitHub Repository](https://github.com/trilokiDA/parking_space_reservation_chatbot)
