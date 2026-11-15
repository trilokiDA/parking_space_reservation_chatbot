# Admin Workflow Testing Guide

This guide shows how to test the complete workflow where customers make reservations and administrators approve/reject them.

## Overview

The workflow has three parts:
1. **Customer**: Makes reservations via the chatbot (main.py)
2. **Administrator**: Reviews and approves/rejects via admin interface (admin_interface.py)
3. **Customer**: Checks status to see admin's decision

## Setup

### 1. Start the Admin Interface (Terminal 1)
```bash
python admin_interface.py
```

This starts:
- Admin CLI for managing reservations
- Admin API server on http://127.0.0.1:8000

You should see:
```
✓ Admin API server started successfully
  URL: http://127.0.0.1:8000
  Health check: http://127.0.0.1:8000/health

Available Commands:
  • 'pending' - View all pending reservations
  • 'approve <id>' - Approve reservation ID
  • 'reject <id>' - Reject reservation ID
  • 'status <id>' - Check status of reservation ID
```

### 2. Start the Customer Chatbot (Terminal 2)
```bash
python main.py
```

## Complete Workflow Test

### Step 1: Customer Makes a Reservation

**In Terminal 2 (Chatbot):**
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

You: 2026-12-25 10:00
Bot: And when would you like to end your parking?

You: 2026-12-25 18:00
Bot: ✓ Reservation created successfully!
     Reservation ID: 8
     Status: Sent to administrator for approval
```

**Note the Reservation ID** (e.g., 8)

### Step 2: Customer Checks Initial Status

**In Terminal 2 (Chatbot):**
```
You: Check status of reservation 8
Bot: 📊 Reservation 8 Status:

     Name: John Doe
     Car: ABC123
     Start: 2026-12-25T10:00:00
     End: 2026-12-25T18:00:00
     Status: pending
```

Status is "pending" - waiting for admin.

### Step 3: Admin Reviews Pending Reservations

**In Terminal 1 (Admin Interface):**
```
Admin> pending

📋 **Pending Reservation Requests**

**Reservation ID: 8**
  Name: John Doe
  Car Number: ABC123
  Start: 2026-12-25T10:00:00
  End: 2026-12-25T18:00:00
  Requested: 2026-11-15T14:30:00
--------------------------------------------------
```

### Step 4: Admin Approves the Reservation

**In Terminal 1 (Admin Interface):**
```
Admin> approve 8
Add notes (optional, press Enter to skip): Approved - parking space A-15 assigned

✓ Reservation 8 approved successfully!
```

### Step 5: Customer Checks Status After Approval

**In Terminal 2 (Chatbot):**
```
You: Check status of reservation 8
Bot: 📊 Reservation 8 Status:

     Name: John Doe
     Car: ABC123
     Start: 2026-12-25T10:00:00
     End: 2026-12-25T18:00:00
     Status: confirmed
     Admin Decision: approved
     Admin Notes: Approved - parking space A-15 assigned
     Decided At: 2026-11-15T14:35:00
```

✅ Customer can now see the admin's decision!

## Testing Rejection

### Step 1: Create Another Reservation

**In Terminal 2 (Chatbot):**
```
You: I need parking
[Complete the flow as before]

Bot: ✓ Reservation created successfully!
     Reservation ID: 9
```

### Step 2: Admin Rejects

**In Terminal 1 (Admin Interface):**
```
Admin> reject 9
Add reason for rejection (optional): Sorry, no spaces available for that time

✓ Reservation 9 rejected.
```

### Step 3: Customer Sees Rejection

**In Terminal 2 (Chatbot):**
```
You: Check status of reservation 9
Bot: 📊 Reservation 9 Status:

     Name: Jane Smith
     Car: XYZ789
     Status: cancelled
     Admin Decision: rejected
     Admin Notes: Sorry, no spaces available for that time
```

## Admin Interface Commands

### View All Pending Reservations
```
Admin> pending
```

### View Specific Reservation Details
```
Admin> details 8
```

### Check Reservation Status
```
Admin> status 8
```

### Approve a Reservation
```
Admin> approve 8
Add notes (optional, press Enter to skip): [your notes]
```

### Reject a Reservation
```
Admin> reject 8
Add reason for rejection (optional): [your reason]
```

### Ask the AI Agent
```
Admin> query How many pending reservations do we have?
```

### Exit
```
Admin> quit
```

## Customer Chatbot Commands

### Make a Reservation
```
You: I want to make a reservation
You: I need parking
You: Book a spot
```

### Check Reservation Status
```
You: Check status of reservation 8
You: What's the status of reservation 8
```

### View All Pending Reservations
```
You: Show me all pending reservations
You: List pending reservations
You: What are the pending reservations
```

### Cancel During Reservation Flow
```
You: cancel
You: quit
You: nevermind
```

## Testing the API Directly

You can also test the admin API directly using curl or Postman:

### Health Check
```bash
curl http://127.0.0.1:8000/health
```

### Add Pending Request
```bash
curl -X POST http://127.0.0.1:8000/admin/pending-request \
  -H "Content-Type: application/json" \
  -d '{
    "reservation_id": 10,
    "reservation_data": {
      "first_name": "Test",
      "last_name": "User",
      "car_number": "TEST123",
      "start_time": "2026-12-25T10:00:00",
      "end_time": "2026-12-25T18:00:00"
    }
  }'
```

### Approve Reservation
```bash
curl -X POST http://127.0.0.1:8000/admin/decision \
  -H "Content-Type: application/json" \
  -d '{
    "reservation_id": 10,
    "decision": "approved",
    "admin_notes": "Approved via API"
  }'
```

## Automated Test

To run an automated test of the complete workflow:

```bash
python test_admin_workflow.py
```

This will:
1. Create a reservation as a customer
2. Simulate admin approval via database
3. Verify customer can see the decision
4. Test rejection workflow
5. Test listing reservations

## Important Notes

### Current Limitation: Admin Agent Uses In-Memory Storage

⚠️ **IMPORTANT**: The current `AdminAgent` class uses in-memory storage (`self.pending_requests`). This means:

- Admin decisions made via the CLI are stored in memory, not the database
- When the admin interface restarts, all pending requests are lost
- The chatbot reads from the database, so it won't see admin decisions unless they're written to the database

### Solution: Update Admin Agent to Use Database

To fix this properly, the `AdminAgent` needs to be updated to:
1. Read reservations from the database instead of in-memory dictionary
2. Write admin decisions back to the database
3. Use the same `DatabaseManager` as the chatbot

This is tracked as a separate enhancement. For now, use the automated test script (`test_admin_workflow.py`) which directly updates the database to simulate admin decisions.

## Verification Checklist

- [ ] Admin interface starts without errors
- [ ] Customer can create reservations
- [ ] Reservations appear in admin's pending list
- [ ] Admin can approve reservations
- [ ] Admin can reject reservations
- [ ] Customer can check status and see admin's decision
- [ ] Customer can see admin's notes
- [ ] API endpoints respond correctly
- [ ] Database is updated with admin decisions

## Troubleshooting

### "Admin API server connection failed"
- Make sure admin_interface.py is running
- Check that port 8000 is not blocked
- Verify the URL in settings (default: http://127.0.0.1:8000)

### "Reservation not found"
- Make sure you're using the correct reservation ID
- Check if the reservation exists in the database
- Verify the database file exists: `data/dynamic_data.db`

### Admin decisions not showing in chatbot
- Ensure both admin and chatbot use the same database
- Check that admin decisions are being written to database
- Try running the automated test to verify the workflow
