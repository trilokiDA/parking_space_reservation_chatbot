># Manual Testing Guide: Complete Admin Workflow

This guide walks you through testing the complete workflow where customers make reservations and administrators approve/reject them.

## Prerequisites

1. Make sure you have run the database migration:
   ```bash
   python migrate_database.py
   ```

2. Make sure your `.env` file has either `OPENAI_API_KEY` or `GROQ_API_KEY`

## Option 1: Using Database-Backed Admin Interface (RECOMMENDED)

This version saves admin decisions to the database, so customers can see them immediately.

### Setup

#### Terminal 1: Start Admin Interface (Database Version)
```bash
python admin_interface_db.py
```

You should see:
```
✓ Admin API server started successfully
  URL: http://127.0.0.1:8000
  Health check: http://127.0.0.1:8000/health

⚠️  NOTE: This version uses the DATABASE instead of in-memory storage
   All admin decisions are saved to the database and visible to customers!

============================================================
    ADMIN RESERVATION MANAGEMENT INTERFACE (DB)
============================================================

Available Commands:
  • 'pending' - View all pending reservations
  • 'approve <id>' - Approve reservation ID
  • 'reject <id>' - Reject reservation ID
  • 'status <id>' - Check status of reservation ID
============================================================

Admin>
```

#### Terminal 2: Start Customer Chatbot
```bash
python main.py
```

### Test Scenario 1: Approval Workflow

#### Step 1: Customer Creates Reservation

In **Terminal 2 (Customer Chatbot)**:
```
You: I want to make a reservation

Bot: I'd be happy to help you make a reservation! Let's collect some information.
     (Type 'cancel' anytime to exit the reservation process)
     First, what is your first name?

You: Alice

Bot: Great! What is your last name?

You: Johnson

Bot: Thank you! What is your car registration number?

You: CAR123

Bot: Perfect! When would you like to start your parking? Please use format: YYYY-MM-DD HH:MM

You: 2026-12-25 09:00

Bot: And when would you like to end your parking? (Same format: YYYY-MM-DD HH:MM)

You: 2026-12-25 17:00

Bot: ✓ Reservation created successfully!

     Reservation ID: 10
     Name: Alice Johnson
     Car: CAR123
     Start: 2026-12-25T09:00:00
     End: 2026-12-25T17:00:00

     Status: Sent to administrator for approval
     You will be notified once an administrator reviews your reservation.

     To check your reservation status, ask: 'Check status of reservation 10'
```

**✏️ Note down the Reservation ID** (e.g., 10)

#### Step 2: Customer Checks Initial Status

In **Terminal 2 (Customer Chatbot)**:
```
You: Check status of reservation 10

Bot: 📊 Reservation 10 Status:

     Name: Alice Johnson
     Car: CAR123
     Start: 2026-12-25T09:00:00
     End: 2026-12-25T17:00:00
     Status: pending
```

✅ Expected: Status should be "pending"

#### Step 3: Admin Views Pending Reservations

In **Terminal 1 (Admin Interface)**:
```
Admin> pending

📋 **Pending Reservation Requests**

**Reservation ID: 10**
  Name: Alice Johnson
  Car Number: CAR123
  Start: 2026-12-25T09:00:00
  End: 2026-12-25T17:00:00
  Created: 2026-11-15T10:30:00
--------------------------------------------------
```

✅ Expected: Should see the new reservation

#### Step 4: Admin Approves Reservation

In **Terminal 1 (Admin Interface)**:
```
Admin> approve 10
Add notes (optional, press Enter to skip): Approved - assigned parking space B-42

✓ Reservation 10 approved successfully and saved to database!
```

✅ Expected: Success message confirming database save

#### Step 5: Customer Sees Admin Approval

In **Terminal 2 (Customer Chatbot)**:
```
You: Check status of reservation 10

Bot: 📊 Reservation 10 Status:

     Name: Alice Johnson
     Car: CAR123
     Start: 2026-12-25T09:00:00
     End: 2026-12-25T17:00:00
     Status: confirmed
     Admin Decision: approved
     Admin Notes: Approved - assigned parking space B-42
     Decided At: 2026-11-15T10:35:00
```

✅ **SUCCESS!** Customer can now see:
- Status changed to "confirmed"
- Admin's decision: "approved"
- Admin's notes with parking space assignment
- When the decision was made

### Test Scenario 2: Rejection Workflow

#### Step 1: Create Another Reservation

In **Terminal 2 (Customer Chatbot)**:
```
You: I need parking
[Follow prompts: Bob, Smith, XYZ789, 2026-12-31 10:00, 2026-12-31 20:00]

Bot: ✓ Reservation created successfully!
     Reservation ID: 11
```

#### Step 2: Admin Rejects Reservation

In **Terminal 1 (Admin Interface)**:
```
Admin> reject 11
Add reason for rejection (optional): Sorry, no spaces available for New Year's Eve

✓ Reservation 11 rejected and saved to database.
```

#### Step 3: Customer Sees Rejection

In **Terminal 2 (Customer Chatbot)**:
```
You: Check status of reservation 11

Bot: 📊 Reservation 11 Status:

     Name: Bob Smith
     Car: XYZ789
     Status: cancelled
     Admin Decision: rejected
     Admin Notes: Sorry, no spaces available for New Year's Eve
```

✅ **SUCCESS!** Customer can see the rejection and reason

### Test Scenario 3: Multiple Pending Reservations

#### Step 1: Create Multiple Reservations

Create 2-3 more reservations following the same process

#### Step 2: View All Pending

In **Terminal 1 (Admin Interface)**:
```
Admin> pending

📋 **Pending Reservation Requests**

**Reservation ID: 12**
  Name: ...
  
**Reservation ID: 13**
  Name: ...
  
**Reservation ID: 14**
  Name: ...
```

In **Terminal 2 (Customer Chatbot)**:
```
You: Show me all pending reservations

Bot: 📋 Pending Reservations (3):

     ID: 12
       Name: ...
       Car: ...
       Start: ...
       End: ...
       Status: pending

     ID: 13
       ...
```

✅ Both admin and customer can see all pending reservations

## Option 2: Automated Test

If you want to run an automated test instead:

```bash
python test_admin_workflow.py
```

This will simulate the complete workflow automatically and verify all steps.

## Common Issues & Solutions

### Issue: "Admin API server connection failed"

**Solution:**
- Make sure `admin_interface_db.py` is running in Terminal 1
- Check that port 8000 is not in use by another application
- Verify the admin API URL in settings

### Issue: "Reservation not found"

**Solution:**
- Double-check the reservation ID number
- Make sure you're using the ID from the most recent reservation
- Verify the database file exists: `data/dynamic_data.db`

### Issue: Admin decisions not visible to customer

**Solution:**
- Make sure you're using `admin_interface_db.py` (the database version)
- NOT the regular `admin_interface.py` (which uses in-memory storage)
- Verify the admin interface shows "saved to database" message

### Issue: "OperationalError: no such column"

**Solution:**
- Run the migration script: `python migrate_database.py`
- This adds the admin decision columns to the database

## Verification Checklist

After testing, verify all these work:

- [ ] Customer can create reservations via chatbot
- [ ] Customer can check reservation status
- [ ] Admin can view all pending reservations
- [ ] Admin can see details of specific reservation
- [ ] Admin can approve reservations
- [ ] Admin approval is saved to database
- [ ] Customer can see admin's approval decision
- [ ] Customer can see admin's notes/comments
- [ ] Admin can reject reservations
- [ ] Admin rejection is saved to database
- [ ] Customer can see admin's rejection reason
- [ ] Both can list all pending reservations
- [ ] Status changes from "pending" to "confirmed" or "cancelled"

## What's Working Now

✅ **Customer Side:**
- Create reservations
- Check status at any time
- See admin decisions immediately
- View all pending reservations
- Get admin's notes and comments

✅ **Admin Side:**
- View all pending requests
- View detailed info for specific reservation
- Approve with custom notes
- Reject with reason
- All decisions saved to database

✅ **Integration:**
- Customer and admin share the same database
- Admin decisions are immediately visible to customers
- No data loss between sessions
- Both interfaces work simultaneously

## Next Steps

After verifying the workflow works:

1. **Replace the old admin interface**: 
   - Rename `admin_interface_db.py` to `admin_interface.py`
   - Update `AdminAgent` to use database
   
2. **Add email notifications**:
   - Send email to customer when admin makes decision
   - Add email field to reservation form

3. **Add more admin features**:
   - Assign specific parking spaces
   - View calendar/schedule
   - Export reports

4. **Add customer features**:
   - Cancel own reservations
   - Modify reservation times
   - View reservation history
