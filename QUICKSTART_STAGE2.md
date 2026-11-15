# Stage 2 Quick Start Guide

This guide will help you quickly set up and demo the Human-in-the-Loop admin approval system.

## Prerequisites

1. Python 3.9+ installed
2. Virtual environment activated
3. API keys configured (OpenAI or Groq)

## Installation (5 minutes)

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

New Stage 2 dependencies:
- `flask` - REST API framework
- `flask-cors` - CORS support  
- `requests` - HTTP client

### 2. Verify environment

Check your `.env` file has the admin API settings:

```env
# Admin API Configuration (Stage 2)
ADMIN_API_URL=http://127.0.0.1:5000
ADMIN_API_PORT=5000
```

If not, copy from `.env.example`.

## Running the Demo (2 terminals required)

### Terminal 1: Start Admin Interface

```bash
python admin_interface.py
```

You should see:
```
✓ Admin API server started successfully
  URL: http://127.0.0.1:5000
  Health check: http://127.0.0.1:5000/health

============================================================
    ADMIN RESERVATION MANAGEMENT INTERFACE
============================================================

Available Commands:
  • 'pending' - View all pending reservations
  • 'details <id>' - View details of reservation ID
  • 'approve <id>' - Approve reservation ID
  • 'reject <id>' - Reject reservation ID
  ...

Admin> _
```

### Terminal 2: Start User Chatbot

```bash
python main.py
```

You should see the chatbot welcome message.

## Demo Flow

### Step 1: Create a Reservation (User Terminal)

```
You: I want to make a reservation

Bot: I'd be happy to help you make a reservation!
     Let's collect some information.
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
     Name: John Doe
     Car: ABC123
     Start: 2024-12-25 14:00
     End: 2024-12-25 18:00

     Status: Sent to administrator for approval
     You will be notified once an administrator reviews your reservation.

     To check your reservation status, ask: 'Check status of reservation 1'
```

### Step 2: View Pending Requests (Admin Terminal)

```
Admin> pending

📋 **Pending Reservation Requests**

**Reservation ID: 1**
  Name: John Doe
  Car Number: ABC123
  Start: 2024-12-25 14:00
  End: 2024-12-25 18:00
  Requested: 2024-11-15T10:30:00
--------------------------------------------------
```

### Step 3: Review Details (Admin Terminal)

```
Admin> details 1

**Reservation Request Details**

Reservation ID: 1
Status: pending

**User Information:**
- Name: John Doe
- Car Registration: ABC123

**Reservation Period:**
- Start Time: 2024-12-25 14:00
- End Time: 2024-12-25 18:00

**Request Metadata:**
- Requested At: 2024-11-15T10:30:00
- Parking Space: Not assigned yet

**Admin Decision:** Pending
```

### Step 4: Approve Reservation (Admin Terminal)

```
Admin> approve 1
Add notes (optional, press Enter to skip): Looks good, approved!

✓ Reservation 1 approved successfully!
```

### Step 5: Use Natural Language Query (Admin Terminal)

```
Admin> query Show me all pending requests

🤖 Agent Response:
Currently, there are no pending reservation requests. All requests have been processed.
```

### Step 6: Check Status Programmatically

You can also check status via REST API:

```bash
curl http://127.0.0.1:5000/api/reservations/1/status
```

Response:
```json
{
  "success": true,
  "status": {
    "reservation_id": 1,
    "status": "approved",
    "admin_decision": "approved",
    "admin_notes": "Looks good, approved!",
    "decided_at": "2024-11-15T10:35:00"
  }
}
```

## Testing the System

### Run Unit Tests

```bash
# Test admin agent (13 tests)
pytest tests/unit/test_admin_agent.py -v

# Test communication service (13 tests)
pytest tests/unit/test_communication_service.py -v

# Run all Stage 2 tests
pytest tests/unit/test_admin_agent.py tests/unit/test_communication_service.py -v
```

Expected output:
```
========================= 26 passed in 0.94s =========================
```

### Test API Endpoints

**Health Check:**
```bash
curl http://127.0.0.1:5000/health
```

**Get Pending Reservations:**
```bash
curl http://127.0.0.1:5000/api/reservations/pending
```

**Approve via API:**
```bash
curl -X POST http://127.0.0.1:5000/api/reservations/1/decide \
  -H "Content-Type: application/json" \
  -d '{"decision": "approved", "notes": "All good"}'
```

## Admin Commands Reference

| Command | Description | Example |
|---------|-------------|---------|
| `pending` | List all pending reservations | `pending` |
| `details <id>` | Show reservation details | `details 1` |
| `approve <id>` | Approve a reservation | `approve 1` |
| `reject <id>` | Reject a reservation | `reject 1` |
| `status <id>` | Check reservation status | `status 1` |
| `query <text>` | Ask AI agent a question | `query Show pending` |
| `help` | Show available commands | `help` |
| `quit` | Exit admin interface | `quit` |

## Troubleshooting

### Issue: Port 5000 already in use

```bash
# On Windows
netstat -ano | findstr :5000
# Kill the process or change port in .env

# On Linux/Mac
lsof -i :5000
kill -9 <PID>
```

### Issue: Cannot connect to admin API

1. Verify admin interface is running
2. Check health endpoint: `curl http://127.0.0.1:5000/health`
3. Check firewall settings

### Issue: "Admin service is currently unavailable"

This message appears when the chatbot cannot reach the admin API. This is expected behavior if:
- Admin interface is not running
- API is on a different port
- Firewall is blocking the connection

The reservation is still saved in the database and will be processed when the admin service is restored.

## Architecture Overview

```
User Chatbot (Terminal 2)
    ↓ Creates reservation
    ↓ Sends via HTTP POST
Admin REST API (Port 5000)
    ↓ Stores in admin agent
Admin Agent (In-memory storage)
    ↓ Displays to admin
Admin Interface (Terminal 1)
    ↓ Admin approves/rejects
    ↓ Updates status
Admin Agent
    ↓ Status available via API
User can check status
```

## Next Steps

1. **Explore AI Query Feature**: Try asking the admin agent natural language questions
2. **Test Multiple Reservations**: Create several reservations and manage them
3. **Check REST API**: Use curl or Postman to test endpoints directly
4. **Review Documentation**: See [STAGE2_README.md](STAGE2_README.md) for detailed docs

## Performance Notes

- API responds in < 100ms for status checks
- Reservation submission takes < 500ms end-to-end
- AI queries take 1-3 seconds (LLM-dependent)
- System supports multiple concurrent admin sessions

## Success Checklist

- [ ] Admin interface starts without errors
- [ ] User chatbot connects successfully
- [ ] Reservation creates and sends to admin
- [ ] Admin can view pending requests
- [ ] Admin can approve/reject reservations
- [ ] Status updates are reflected correctly
- [ ] All 26 tests pass

## For Production

Consider these improvements for production deployment:

1. **Persistence**: Replace in-memory storage with database
2. **Authentication**: Add API key or OAuth for admin endpoints
3. **Notifications**: Implement email/SMS alerts
4. **Web Dashboard**: Create React/Vue admin interface
5. **Scalability**: Use Redis for session management
6. **Monitoring**: Add logging and metrics collection

---

**Congratulations!** You've successfully set up the Stage 2 Human-in-the-Loop system! 🎉
