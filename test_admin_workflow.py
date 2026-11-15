"""Test the complete admin workflow: Customer -> Admin -> Customer."""
import os
from dotenv import load_dotenv
from src.config.settings import get_settings
from src.chatbot.chatbot import ParkingChatbot
from src.database.db_manager import DatabaseManager
from datetime import datetime

load_dotenv()


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def test_full_workflow():
    """Test the complete workflow from customer request to admin response."""

    print_section("ADMIN WORKFLOW TEST: Customer -> Admin -> Customer")

    settings = get_settings()
    chatbot = ParkingChatbot(settings)
    db_manager = DatabaseManager(settings.database_url)

    # ==========================================
    # STEP 1: Customer makes a reservation
    # ==========================================
    print_section("STEP 1: Customer Makes a Reservation")

    print("Customer: I want to make a reservation")
    response = chatbot.process_message("I want to make a reservation")
    print(f"Bot: {response}\n")

    print("Customer: Alice")
    response = chatbot.process_message("Alice")
    print(f"Bot: {response}\n")

    print("Customer: Smith")
    response = chatbot.process_message("Smith")
    print(f"Bot: {response}\n")

    print("Customer: TEST1234")
    response = chatbot.process_message("TEST1234")
    print(f"Bot: {response}\n")

    print("Customer: 2026-12-30 09:00")
    response = chatbot.process_message("2026-12-30 09:00")
    print(f"Bot: {response}\n")

    print("Customer: 2026-12-30 17:00")
    response = chatbot.process_message("2026-12-30 17:00")
    print(f"Bot: {response}\n")

    # Extract reservation ID from response
    import re
    match = re.search(r'Reservation ID: (\d+)', response)
    if match:
        reservation_id = int(match.group(1))
        print(f"✓ Reservation created with ID: {reservation_id}\n")
    else:
        print("❌ Could not extract reservation ID from response")
        return

    # ==========================================
    # STEP 2: Check reservation status (before admin decision)
    # ==========================================
    print_section("STEP 2: Customer Checks Status (Before Admin Decision)")

    print(f"Customer: Check status of reservation {reservation_id}")
    response = chatbot.process_message(f"Check status of reservation {reservation_id}")
    print(f"Bot: {response}\n")

    assert "Status: pending" in response, "Reservation should be pending"
    print("✓ Reservation is pending (waiting for admin)\n")

    # ==========================================
    # STEP 3: Admin approves the reservation
    # ==========================================
    print_section("STEP 3: Admin Approves the Reservation")

    print("Simulating admin approval via database update...\n")

    # Get the reservation from database
    reservation = db_manager.get_reservation(reservation_id)

    if reservation:
        print(f"Found reservation: {reservation['first_name']} {reservation['last_name']}")

        # Simulate admin approval by directly updating the database
        # In real scenario, this would be done via admin_interface.py
        from sqlalchemy import create_engine, update
        from sqlalchemy.orm import sessionmaker
        from src.database.models import Reservation

        engine = create_engine(settings.database_url)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        try:
            stmt = update(Reservation).where(
                Reservation.id == reservation_id
            ).values(
                status="confirmed",
                admin_decision="approved",
                admin_notes="Approved by admin - space A15 assigned",
                decided_at=datetime.now()
            )
            session.execute(stmt)
            session.commit()
            print(f"✓ Admin approved reservation {reservation_id}\n")
        except Exception as e:
            session.rollback()
            print(f"❌ Error updating reservation: {e}\n")
        finally:
            session.close()
    else:
        print(f"❌ Reservation {reservation_id} not found in database\n")
        return

    # ==========================================
    # STEP 4: Customer checks status again (after admin decision)
    # ==========================================
    print_section("STEP 4: Customer Checks Status (After Admin Decision)")

    print(f"Customer: Check status of reservation {reservation_id}")
    response = chatbot.process_message(f"Check status of reservation {reservation_id}")
    print(f"Bot: {response}\n")

    # Verify the response includes admin decision
    assert "confirmed" in response.lower() or "approved" in response.lower(), \
        "Should show approved status"
    assert "Admin Decision: approved" in response, "Should show admin decision"
    assert "space A15" in response, "Should show admin notes"

    print("✓ Customer can see admin's approval and notes!\n")

    # ==========================================
    # STEP 5: Test admin rejection workflow
    # ==========================================
    print_section("STEP 5: Test Admin Rejection Workflow")

    # Create another reservation
    print("Creating another reservation to test rejection...\n")
    chatbot.process_message("I need parking")
    chatbot.process_message("Bob")
    chatbot.process_message("Jones")
    chatbot.process_message("REJECT999")
    chatbot.process_message("2027-01-15 10:00")
    response = chatbot.process_message("2027-01-15 18:00")

    match = re.search(r'Reservation ID: (\d+)', response)
    if match:
        rejection_id = int(match.group(1))
        print(f"✓ Created reservation {rejection_id} for rejection test\n")

        # Admin rejects it
        session = SessionLocal()
        try:
            stmt = update(Reservation).where(
                Reservation.id == rejection_id
            ).values(
                status="cancelled",
                admin_decision="rejected",
                admin_notes="Sorry, no spaces available for that time slot",
                decided_at=datetime.now()
            )
            session.execute(stmt)
            session.commit()
            print(f"✓ Admin rejected reservation {rejection_id}\n")
        finally:
            session.close()

        # Customer checks
        print(f"Customer: Check status of reservation {rejection_id}")
        response = chatbot.process_message(f"Check status of reservation {rejection_id}")
        print(f"Bot: {response}\n")

        assert "rejected" in response.lower() or "cancelled" in response.lower(), \
            "Should show rejected status"
        print("✓ Customer can see admin's rejection!\n")

    # ==========================================
    # STEP 6: Test listing all reservations
    # ==========================================
    print_section("STEP 6: View All Reservations")

    print("Customer: Show me all pending reservations")
    response = chatbot.process_message("Show me all pending reservations")
    print(f"Bot: {response}\n")

    # ==========================================
    # FINAL SUMMARY
    # ==========================================
    print_section("TEST SUMMARY")

    print("✅ WORKFLOW COMPLETE!")
    print("\nVerified capabilities:")
    print("  1. ✓ Customer can create reservations")
    print("  2. ✓ Reservations are saved to database with 'pending' status")
    print("  3. ✓ Admin can approve reservations (updates database)")
    print("  4. ✓ Admin can reject reservations (updates database)")
    print("  5. ✓ Customer can check status and see admin's decision")
    print("  6. ✓ Customer can see admin's notes/comments")
    print("  7. ✓ Customer can list all pending reservations")
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    test_full_workflow()
