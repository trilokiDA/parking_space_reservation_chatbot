# Stage 4: LangGraph Orchestration - Complete System Integration

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Latest-green.svg)](https://langchain-ai.github.io/langgraph/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Overview

Stage 4 implements **LangGraph-based orchestration** to seamlessly integrate all three previous stages into a unified, state-driven workflow. This creates an intelligent system where:

1. **RAG Chatbot** (Stage 1) handles user interactions and information retrieval
2. **Admin Agent** (Stage 2) provides human-in-the-loop approval
3. **MCP Server** (Stage 3) processes and stores confirmed reservations

All components are orchestrated through a **LangGraph state machine** that manages the complete reservation lifecycle.

## 🏗️ Architecture

### Workflow Graph Structure

```
                    ┌─────────────────────┐
                    │   User Input        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ User Interaction    │◄── RAG Chatbot
                    │ Node                │   (Stage 1)
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Is Reservation?     │
                    └──────┬──────────────┘
                           │
                ┌──────────┴──────────┐
                │                     │
            No  │                     │ Yes
                │                     │
                ▼                     ▼
         ┌──────────┐      ┌─────────────────────┐
         │   END    │      │  Admin Approval     │◄── Admin Agent
         └──────────┘      │  Node               │   (Stage 2)
                           └──────────┬──────────┘
                                      │
                                      ▼
                           ┌─────────────────────┐
                           │  Approved?          │
                           └──────┬──────────────┘
                                  │
                       ┌──────────┴──────────┐
                       │                     │
                  Yes  │                     │ No
                       │                     │
                       ▼                     ▼
            ┌─────────────────────┐  ┌─────────────────────┐
            │  MCP Processing     │  │ User Notification   │
            │  Node               │◄─┤  (Rejected)         │
            └──────────┬──────────┘  └─────────────────────┘
                       │                       │
                       ▼                       │
            ┌─────────────────────┐            │
            │  User Notification  │            │
            │  (Approved)         │            │
            └──────────┬──────────┘            │
                       │                       │
                       └───────────┬───────────┘
                                   │
                                   ▼
                            ┌──────────┐
                            │   END    │
                            └──────────┘
```

### State Management

The workflow uses a typed state dictionary (`ReservationWorkflowState`) that tracks:

- **User interaction**: Messages and conversation history
- **Reservation data**: ID, status, and details
- **Workflow stage**: Current position in the graph
- **Admin decisions**: Approval/rejection with notes
- **Metadata**: Timestamps, errors, retry counts

### LangGraph Nodes

1. **`user_interaction_node`**: Processes user messages through RAG chatbot
2. **`check_reservation_node`**: Looks up reservation status
3. **`admin_approval_node`**: Checks admin decision from database
4. **`mcp_processing_node`**: Writes approved reservations via MCP server
5. **`user_notification_node`**: Notifies user of final status

### Conditional Edges

- **`should_proceed_to_approval`**: Routes to approval if reservation created
- **`check_reservation_status`**: Determines if approval needed
- **`check_admin_decision`**: Routes based on approved/rejected/pending

## 🚀 Quick Start

### Prerequisites

Ensure you have completed Stages 1-3:
- ✅ RAG chatbot initialized
- ✅ Admin agent configured
- ✅ MCP server running

### Installation

```bash
# LangGraph should already be installed, but if not:
pip install langgraph langchain-core

# Verify installation
python -c "import langgraph; print('LangGraph:', langgraph.__version__)"
```

### Running the Orchestrated System

#### Option 1: Single Terminal (Recommended for Testing)

```bash
# Start the orchestrated main application
python orchestrated_main.py
```

#### Option 2: Multi-Terminal (Full System)

**Terminal 1 - MCP Server:**
```bash
python run_mcp_server.py
```

**Terminal 2 - Admin Interface:**
```bash
python admin_interface_db.py
```

**Terminal 3 - Orchestrated Chatbot:**
```bash
python orchestrated_main.py
```

## 📖 Usage Examples

### Example 1: Information Query

```
🗣️  You: What are your operating hours?

🔄 Processing through workflow...

🤖 Bot: Our parking facility operates 24/7, allowing you to park
and retrieve your vehicle at any time of day or night.

💬 Workflow Stage: User Interaction
```

### Example 2: Complete Reservation Flow

```
🗣️  You: I want to make a reservation

🔄 Processing through workflow...

🤖 Bot: I'd be happy to help you make a reservation! Let's collect
some information. First, what is your first name?

💬 Workflow Stage: User Interaction

🗣️  You: John

🤖 Bot: Great! What is your last name?

🗣️  You: Doe

🤖 Bot: Thank you! What is your car registration number?

🗣️  You: ABC123

🤖 Bot: Perfect! When would you like to start your parking?

🗣️  You: 2024-12-25 14:00

🤖 Bot: And when would you like to end your parking?

🗣️  You: 2024-12-25 18:00

🤖 Bot: ✓ Reservation created successfully!
        Reservation ID: 15
        Status: Sent to administrator for approval

⏳ Workflow Stage: Awaiting Approval

📋 Reservation ID: 15
💡 Tip: An administrator will review your request.
     Check status with: 'Check status of reservation 15'
```

### Example 3: Status Check

```
🗣️  You: Check status of reservation 15

🔄 Processing through workflow...

🤖 Bot: Reservation #15 Status: Approved
        Your parking space has been confirmed!

✅ Workflow Stage: Completed
```

### Example 4: Viewing Statistics

```
🗣️  You: stats

============================================================
📊 PERFORMANCE STATISTICS
============================================================
total_queries: 42
average_latency_ms: 245.3
recall@3: 0.850
precision@3: 0.780
mrr: 0.820
============================================================
```

## 🧪 Testing

### Run All Tests

```bash
# Run all Stage 4 tests
pytest tests/unit/test_orchestration.py tests/integration/test_full_workflow.py -v

# Run with coverage
pytest tests/unit/test_orchestration.py tests/integration/test_full_workflow.py --cov=src.orchestration --cov-report=html
```

### Unit Tests

```bash
# Test orchestrator components
pytest tests/unit/test_orchestration.py -v

# Specific test classes
pytest tests/unit/test_orchestration.py::TestReservationOrchestrator -v
pytest tests/unit/test_orchestration.py::TestWorkflowStateTransitions -v
```

### Integration Tests

```bash
# Test complete workflow
pytest tests/integration/test_full_workflow.py -v

# Specific test classes
pytest tests/integration/test_full_workflow.py::TestCompleteWorkflow -v
pytest tests/integration/test_full_workflow.py::TestWorkflowPerformance -v
pytest tests/integration/test_full_workflow.py::TestWorkflowEdgeCases -v
```

### Test Coverage

Our test suite covers:

- ✅ **Unit Tests** (27 tests):
  - Orchestrator initialization
  - Individual node functions
  - State transitions
  - Conditional edge logic
  - Reservation ID extraction
  - Error handling

- ✅ **Integration Tests** (12 tests):
  - Complete workflow execution
  - Multi-stage reservation flow
  - Status checking
  - Approval/rejection flows
  - Performance benchmarks
  - Edge cases and error scenarios

## 📊 System Components

### ReservationOrchestrator Class

Main orchestration class that:
- Initializes all Stage 1-3 components
- Builds the LangGraph workflow
- Manages state transitions
- Handles errors and retries

**Key Methods:**

```python
# Process user input through complete workflow
orchestrator.process_user_input(
    user_message="I want to make a reservation",
    thread_id="user_session_123"
)

# Check workflow status
orchestrator.get_workflow_status(reservation_id=15)
```

### ReservationWorkflowState

TypedDict containing:

```python
{
    "user_message": str,              # Current user input
    "chatbot_response": str,          # Bot's response
    "conversation_history": list,     # Full conversation
    "reservation_id": Optional[int],  # Created reservation ID
    "reservation_data": Optional[Dict], # Reservation details
    "current_stage": str,             # Workflow position
    "admin_decision": Optional[str],  # Approval status
    "admin_notes": Optional[str],     # Admin comments
    "timestamp": str,                 # ISO timestamp
    "error_message": Optional[str],   # Any errors
    "retry_count": int                # Retry attempts
}
```

## 🔧 Configuration

### Environment Variables

Stage 4 uses the same `.env` configuration as previous stages:

```env
# LLM Provider
OPENAI_API_KEY=your_openai_key
GROQ_API_KEY=your_groq_key  # Optional
LLM_PROVIDER=openai  # or "groq"

# Models
LLM_MODEL=gpt-3.5-turbo
EMBEDDING_MODEL=text-embedding-3-small

# Database
DATABASE_URL=sqlite:///parking_reservation.db

# MCP Server (Stage 3)
MCP_SERVER_API_KEY=your_mcp_api_key
MCP_SERVER_URL=http://127.0.0.1:8001

# Admin API (Stage 2)
ADMIN_API_URL=http://127.0.0.1:8000
```

### Workflow Customization

You can customize the workflow graph in `src/orchestration/workflow_graph.py`:

```python
# Add new nodes
workflow.add_node("custom_node", custom_function)

# Modify conditional edges
workflow.add_conditional_edges(
    "node_name",
    decision_function,
    {
        "path1": "next_node_1",
        "path2": "next_node_2"
    }
)

# Add new edges
workflow.add_edge("node_a", "node_b")
```

## 📈 Performance Metrics

### Workflow Performance

- **Average end-to-end latency**: < 2 seconds (simple queries)
- **Reservation creation latency**: < 5 seconds
- **State persistence**: Automatic via MemorySaver
- **Concurrent handling**: Supports multiple threads

### System Throughput

- **User interactions**: 100+ queries/minute
- **Admin approvals**: Real-time updates
- **MCP writes**: ~50 reservations/second

## 🔍 Monitoring and Debugging

### Logging

Logs are written to:
- **Console**: INFO level and above
- **File**: `orchestrated_chatbot.log` (all levels)

```python
import logging
logger = logging.getLogger(__name__)
```

### State Inspection

Use LangGraph's built-in state tracking:

```python
# Get current state
current_state = workflow.get_state(config)

# View state history
state_history = workflow.get_state_history(config)
```

### Debug Mode

Enable debug logging:

```bash
# Set environment variable
export LOG_LEVEL=DEBUG

# Or modify in code
logging.basicConfig(level=logging.DEBUG)
```

## 🚨 Error Handling

The orchestrator implements robust error handling:

1. **Node-level errors**: Caught and logged, state marked with error
2. **Workflow errors**: Graceful degradation, user notification
3. **Retry logic**: Configurable retry count in state
4. **State recovery**: Automatic checkpoint management

### Common Issues

**Issue**: `ImportError: No module named 'langgraph'`
```bash
# Solution
pip install langgraph langchain-core
```

**Issue**: Workflow hangs at approval stage
```bash
# Solution: Check admin interface is running
python admin_interface_db.py
```

**Issue**: MCP write fails
```bash
# Solution: Verify MCP server is running and API key is correct
python run_mcp_server.py
```

## 📚 Additional Resources

### Documentation

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangChain Documentation](https://python.langchain.com/)
- [Stage 1 README](README.md)
- [Stage 2 README](STAGE2_README.md)
- [Stage 3 README](STAGE3_README.md)

### Code Structure

```
src/orchestration/
├── __init__.py
└── workflow_graph.py          # Main orchestrator implementation

tests/
├── unit/
│   └── test_orchestration.py  # Unit tests
└── integration/
    └── test_full_workflow.py  # Integration tests

orchestrated_main.py           # Main entry point
```

## 🎓 Advanced Usage

### Custom Workflow Nodes

Add custom processing nodes:

```python
def custom_processing_node(state: ReservationWorkflowState) -> ReservationWorkflowState:
    """Custom processing logic."""
    # Your logic here
    state["custom_field"] = "processed"
    return state

# Add to workflow
workflow.add_node("custom_processing", custom_processing_node)
```

### Conditional Routing

Implement complex routing logic:

```python
def custom_router(state: ReservationWorkflowState) -> str:
    """Custom routing decision."""
    if state.get("special_condition"):
        return "special_path"
    return "normal_path"

workflow.add_conditional_edges(
    "decision_node",
    custom_router,
    {
        "special_path": "special_node",
        "normal_path": "normal_node"
    }
)
```

### State Persistence

Access checkpointed state:

```python
# Get latest checkpoint
checkpoint = workflow.get_state(config)

# Resume from checkpoint
result = workflow.invoke(new_input, config)
```

## ✅ Stage 4 Checklist

- [x] LangGraph orchestration implemented
- [x] All components integrated (Stages 1-3)
- [x] State management with typed dictionaries
- [x] Conditional edge routing
- [x] Error handling and recovery
- [x] Unit tests (27 tests)
- [x] Integration tests (12 tests)
- [x] Documentation complete
- [x] Performance benchmarks
- [x] Example usage scenarios

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

## 📧 Support

For issues or questions:
- Open an issue on GitHub
- Check existing documentation
- Review test examples

---

**Stage 4 Complete** ✅ - Full LangGraph orchestration with seamless integration of all components!

**Next Steps**: Deploy to production, add monitoring, implement advanced features (email notifications, web dashboard, multi-language support)
