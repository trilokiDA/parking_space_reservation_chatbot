# Quick Start Guide - Stage 3

## 5-Minute Setup

### 1. Install New Dependencies

```bash
pip install fastapi uvicorn
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variable (Optional)

Add to `.env` file:
```env
MCP_SERVER_API_KEY=your_secure_api_key_here
```

If not set, a temporary key will be generated automatically.

### 3. Start All Services

Open **3 terminals**:

**Terminal 1 - MCP Server:**
```bash
python run_mcp_server.py
```

Copy the API key shown in the output!

**Terminal 2 - Admin Interface:**
```bash
python admin_interface_db.py
```

**Terminal 3 - User Chatbot:**
```bash
python main.py
```

### 4. Test the Complete Flow

**In Terminal 3 (User):**
```
You: I want to make a reservation
```
Follow the prompts to create a reservation.

**In Terminal 2 (Admin):**
```
Admin> pending
Admin> approve 1
```

**Check the Result:**
```bash
cat data/confirmed_reservations.txt
```

You should see your approved reservation written in the format:
```
John Doe | ABC123 | 2024-12-25 14:00 to 2024-12-25 18:00 | 2024-12-24 10:30:15
```

## Verify MCP Server is Working

### Health Check
```bash
curl http://127.0.0.1:8001/health
```

### Manual Write Test
```bash
curl -X POST http://127.0.0.1:8001/api/v1/reservations/write \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "reservation_id": 999,
    "first_name": "Test",
    "last_name": "User",
    "car_number": "TEST123",
    "start_time": "2024-12-25T14:00:00",
    "end_time": "2024-12-25T18:00:00"
  }'
```

## Running Tests

```bash
# All Stage 3 tests
pytest tests/unit/test_mcp_server.py -v

# Integration tests
pytest tests/integration/test_stage3_integration.py -v

# With coverage
pytest tests/unit/test_mcp_server.py --cov=src/mcp_server --cov-report=term
```

## Troubleshooting

### Port Already in Use
```bash
# Windows
netstat -ano | findstr :8001

# Linux/Mac
lsof -i :8001
```

Kill the process or change the port in `run_mcp_server.py`.

### File Not Created
Check that `data/` directory exists:
```bash
mkdir -p data
```

### Authentication Error
Make sure you're using the correct API key from the MCP server startup output.

## What's New in Stage 3?

1. ✅ **MCP Server**: FastAPI-based server for processing reservations
2. ✅ **File Writing**: Approved reservations automatically written to file
3. ✅ **API Security**: API key authentication
4. ✅ **Integration**: Seamless integration with Stage 2 admin workflow
5. ✅ **Testing**: Comprehensive unit and integration tests

## Next Steps

- Review [STAGE3_README.md](STAGE3_README.md) for detailed documentation
- Explore the API at `http://127.0.0.1:8001/docs` (FastAPI auto-docs)
- Check confirmed reservations in `data/confirmed_reservations.txt`
- Run the test suite to verify everything works

## Support

Having issues? Check:
1. All three services are running
2. API key is correct
3. Dependencies are installed
4. Ports 5001 and 8001 are available
5. Run tests: `pytest tests/unit/test_mcp_server.py -v`
