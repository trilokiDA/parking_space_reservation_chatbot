"""Check reservation 13 details."""
from src.database.db_manager import DatabaseManager
from src.config.settings import get_settings

db = DatabaseManager(get_settings().database_url)
res = db.get_reservation(13)

if res:
    print('Reservation 13 Details:')
    print(f'  ID: {res["id"]}')
    print(f'  Status: {res["status"]}')
    print(f'  Name: {res["first_name"]} {res["last_name"]}')
    print(f'  Car: {res["car_number"]}')
    print(f'  Admin Decision: {res["admin_decision"]}')
    print(f'  Admin Notes: {res["admin_notes"]}')
    print(f'  Start Time: {res["start_time"]}')
    print(f'  End Time: {res["end_time"]}')
    print(f'  Decided At: {res["decided_at"]}')
else:
    print('Reservation 13 not found!')
