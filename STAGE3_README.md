# Stage 3: MCP Server Integration

## Overview

Stage 3 implements a secure MCP (Model Context Protocol) server using Python and FastAPI to process confirmed reservations. When an administrator approves a reservation, the system automatically writes the reservation details to a text file in a standardized format.

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌──────────────┐      ┌─────────────┐
│   User      │─────>│   Chatbot    │─────>│  Database    │      │   MCP       │
│  (Main.py)  │      │  (Stage 1)   │      │              │      │  Server     │
└─────────────┘      └──────────────┘      └──────────────┘      └─────────────┘
                                                   │                      ▲
                                                   │                      │
                                                   ▼                      │
                                            ┌──────────────┐              │
                                            │    Admin     │──────────────┘
                                            │   Agent      │   Write confirmed
                                            │  (Stage 2)   │   reservations
                                            └──────────────┘
```

## Features

### 1. **MCP Server (FastAPI)**
- **RESTful API** with FastAPI framework
- **Secure authentication** using API key
- **File writing** with thread-safe operations
- **CORS support** for cross-origin requests
- **Health monitoring** endpoint
- **Input validation** using Pydantic models

### 2. **File Format**
Reservations are written in the format:
```
Name | Car Number | Reservation Period | Approval Time
```

Example:
```
John Doe | ABC123 | 2024-12-25 14:00 to 2024-12-25 18:00 | 2024-12-24 10:30:15
```

### 3. **Security Features**
- **API Key Authentication**: All endpoints require valid API key
- **Input Validation**: Strict validation of all input data
- **Thread-Safe File Operations**: Prevents race conditions
- **File Locking**: Ensures data integrity during writes
- **CORS Configuration**: Controlled cross-origin access

### 4. **Integration**
- Seamlessly integrates with existing Stage 1 and Stage 2 components
- Admin agent automatically sends approved reservations to MCP server
- Database remains the source of truth
- File serves as an audit log

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

The new dependencies for Stage 3:
- `fastapi>=0.115.0` - Modern web framework
- `uvicorn>=0.32.0` - ASGI server
- `requests>=2.31.0` - HTTP client (already included in Stage 2)

### 2. Environment Setup

Add to your `.env` file:

```env
# Stage 3: MCP Server
MCP_SERVER_API_KEY=your_secure_api_key_here
```

If not set, the server will generate a temporary API key on startup.

## Usage

### Running the Complete System (3 Terminals)

**Terminal 1 - MCP Server:**
```bash
python run_mcp_server.py
```

Output:
```
======================================================================
🚀 MCP SERVER - STAGE 3
======================================================================
📝 Data File: C:\...\data\confirmed_reservations.txt
🔑 API Key: <your-api-key>
🌐 Server URL: http://127.0.0.1:8001
💚 Health Check: http://127.0.0.1:8001/health
======================================================================
```

**Terminal 2 - Admin Interface:**
```bash
python admin_interface_db.py
```

**Terminal 3 - User Chatbot:**
```bash
python main.py
```

### Workflow Example

1. **User makes a reservation** (Terminal 3):
```
You: I want to make a reservation
Bot: Let's collect some information. What is your first name?
You: John
Bot: What is your last name?
You: Doe
Bot: What is your car registration number?
You: ABC123
Bot: When would you like to start your parking? (YYYY-MM-DD HH:MM)
You: 2024-12-25 14:00
Bot: When would you like to end your parking?
You: 2024-12-25 18:00
Bot: ✓ Reservation created successfully! Reservation ID: 1
```

2. **Admin approves** (Terminal 2):
```
Admin> pending
📋 **Pending Reservation Requests**

**Reservation ID: 1**
  Name: John Doe
  Car Number: ABC123
  Start: 2024-12-25 14:00:00
  End: 2024-12-25 18:00:00

Admin> approve 1
Add notes (optional): Regular customer, approved
✓ Reservation 1 approved successfully and saved to database!
```

3. **Reservation written to file** (Automatic via MCP Server):
The approved reservation is automatically written to `data/confirmed_reservations.txt`:
```
John Doe | ABC123 | 2024-12-25 14:00 to 2024-12-25 18:00 | 2024-12-24 10:30:15 | Notes: Regular customer, approved
```

## API Endpoints

### 1. Root Endpoint
```http
GET /
```

Response:
```json
{
  "service": "Reservation MCP Server",
  "version": "1.0.0",
  "status": "running"
}
```

### 2. Health Check
```http
GET /health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-11-16T10:30:00",
  "file_exists": true,
  "file_path": "/path/to/confirmed_reservations.txt"
}
```

### 3. Write Reservation
```http
POST /api/v1/reservations/write
Headers: X-API-Key: <your-api-key>
Content-Type: application/json
```

Request Body:
```json
{
  "reservation_id": 1,
  "first_name": "John",
  "last_name": "Doe",
  "car_number": "ABC123",
  "start_time": "2024-12-25T14:00:00",
  "end_time": "2024-12-25T18:00:00",
  "approval_time": "2024-12-24T10:30:15",
  "admin_notes": "Regular customer"
}
```

Response:
```json
{
  "success": true,
  "message": "Reservation successfully written to file",
  "reservation_id": 1,
  "file_path": "/path/to/confirmed_reservations.txt"
}
```

### 4. List Reservations
```http
GET /api/v1/reservations/list?limit=100
Headers: X-API-Key: <your-api-key>
```

Response:
```json
{
  "count": 5,
  "total_count": 10,
  "reservations": [
    "John Doe | ABC123 | 2024-12-25 14:00 to 18:00 | 2024-12-24 10:30:15",
    "..."
  ]
}
```

## Testing

### Run All Tests

```bash
# All tests
pytest

# Only Stage 3 tests
pytest tests/unit/test_mcp_server.py -v

# Integration tests
pytest tests/integration/test_stage3_integration.py -v

# With coverage
pytest tests/unit/test_mcp_server.py --cov=src/mcp_server --cov-report=html
```

### Test Coverage

Stage 3 includes comprehensive tests:

**Unit Tests** (`tests/unit/test_mcp_server.py`):
- ✅ MCP Server API endpoints
- ✅ Authentication and authorization
- ✅ Input validation
- ✅ File writing operations
- ✅ MCP Client functionality
- ✅ Security features
- ✅ Concurrent operations

**Integration Tests** (`tests/integration/test_stage3_integration.py`):
- ✅ End-to-end approval workflow
- ✅ Database-MCP server integration
- ✅ Data consistency
- ✅ Error handling
- ✅ Complete system flow

## File Structure

```
intelligent_chatbot/
├── src/
│   ├── mcp_server/
│   │   ├── __init__.py
│   │   ├── mcp_server.py          # FastAPI server
│   │   └── mcp_client.py          # Client for server communication
│   └── admin_agent/
│       └── admin_agent_db.py      # Updated with MCP integration
├── data/
│   └── confirmed_reservations.txt # Output file
├── tests/
│   ├── unit/
│   │   └── test_mcp_server.py     # MCP unit tests
│   └── integration/
│       └── test_stage3_integration.py  # Integration tests
├── run_mcp_server.py              # Server startup script
└── STAGE3_README.md               # This file
```

## Security Considerations

### 1. **API Key Management**
- Store API keys in environment variables, never in code
- Use strong, randomly generated keys
- Rotate keys periodically
- Different keys for development and production

### 2. **Input Validation**
- All inputs validated using Pydantic models
- Type checking enforced
- Length constraints on string fields
- Date range validation

### 3. **File Access**
- Thread-safe file operations
- File locking on Unix systems
- Proper error handling
- Automatic directory creation with safe permissions

### 4. **CORS Configuration**
- Configure specific allowed origins in production
- Credentials handling controlled
- HTTP methods restricted

### 5. **Logging**
- All operations logged
- No sensitive data in logs
- Structured logging format
- Error tracking

## Production Deployment

### 1. **Environment Variables**
```env
MCP_SERVER_API_KEY=<strong-random-key>
MCP_SERVER_HOST=0.0.0.0  # For production
MCP_SERVER_PORT=8001
```

### 2. **Running with Gunicorn** (Production)
```bash
pip install gunicorn
gunicorn src.mcp_server.mcp_server:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8001
```

### 3. **Docker Deployment** (Optional)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "run_mcp_server.py"]
```

### 4. **Systemd Service** (Linux)
```ini
[Unit]
Description=MCP Reservation Server
After=network.target

[Service]
Type=simple
User=<your-user>
WorkingDirectory=/path/to/intelligent_chatbot
Environment="MCP_SERVER_API_KEY=<your-key>"
ExecStart=/path/to/venv/bin/python run_mcp_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## Troubleshooting

### Issue: MCP Server won't start

**Check 1**: Port already in use
```bash
# Windows
netstat -ano | findstr :8001

# Linux/Mac
lsof -i :8001
```

**Solution**: Kill the process or use a different port

**Check 2**: Missing dependencies
```bash
pip install fastapi uvicorn --upgrade
```

### Issue: Authentication fails

**Check**: API key mismatch
```python
# Verify API key in environment
import os
print(os.getenv("MCP_SERVER_API_KEY"))
```

**Solution**: Ensure the same API key is used in server and client

### Issue: File not being created

**Check**: Directory permissions
```bash
# Create data directory
mkdir -p data
chmod 755 data
```

**Solution**: Ensure the application has write permissions

### Issue: Reservation not written after approval

**Check 1**: MCP server running?
```bash
curl http://127.0.0.1:8001/health
```

**Check 2**: Check admin agent logs
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance Considerations

### 1. **Concurrency**
- FastAPI is async-capable
- Thread-safe file operations
- Can handle multiple simultaneous requests
- Use proper worker configuration in production

### 2. **File Size Management**
- File grows with each reservation
- Consider log rotation for production
- Archive old reservations periodically

### 3. **Monitoring**
- Health check endpoint for monitoring
- Structured logging for analysis
- Track response times
- Monitor file size growth

## Future Enhancements

### Potential Improvements:
1. **Database File Writer**: Store in database instead of text file
2. **Cloud Storage**: Upload to S3/Azure Blob/GCS
3. **Notification Service**: Send emails/SMS on approval
4. **Webhook Support**: Notify external systems
5. **Backup Service**: Automated backups
6. **Metrics Dashboard**: Real-time monitoring
7. **Rate Limiting**: Prevent abuse
8. **Multiple Output Formats**: JSON, CSV, XML
9. **Reservation Search**: Query capabilities
10. **Admin Dashboard**: Web UI for file management

## Integration with Stages 1 & 2

### Stage 1 Integration
- Uses existing database models
- Preserves reservation data flow
- No changes to user-facing chatbot

### Stage 2 Integration
- Admin agent updated with MCP client
- Automatic file write on approval
- Maintains database as source of truth
- File serves as audit log

### Data Flow
```
User Request (Stage 1)
    ↓
Database (Pending)
    ↓
Admin Review (Stage 2)
    ↓
Admin Approval
    ↓
Database Update (Confirmed)
    ↓
MCP Server (Stage 3) ← NEW
    ↓
File Write (Audit Log)
```

## Support

For issues or questions:
1. Check the logs: `tail -f <log-file>`
2. Verify all services are running
3. Check API key configuration
4. Review error messages
5. Run tests: `pytest tests/unit/test_mcp_server.py -v`

## License

MIT License - See LICENSE file for details

---

**Stage 3 Complete** ✅
- ✅ FastAPI-based MCP server
- ✅ Secure API key authentication
- ✅ File-based reservation storage
- ✅ Integration with Stage 2 admin approval
- ✅ Comprehensive test coverage
- ✅ Production-ready deployment options
