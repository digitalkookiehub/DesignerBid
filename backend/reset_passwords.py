"""Reset all user passwords to Designer@123"""
from app.database import SessionLocal
from app.models.user import User
from app.auth.jwt import hash_password

db = SessionLocal()
for u in db.query(User).all():
    u.hashed_password = hash_password("Designer@123")
    print("Updated:", u.email)
db.commit()
db.close()
print("All passwords reset to: Designer@123")
