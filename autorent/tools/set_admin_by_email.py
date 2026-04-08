import sys

from app.database import SessionLocal
from app.models.user import User


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python tools/set_admin_by_email.py user@example.com")
        return 2

    email = sys.argv[1].strip().lower()
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print("USER_NOT_FOUND")
            return 1

        db.query(User).filter(User.role == "admin").update({"role": "user"})
        user.role = "admin"
        user.is_verified = True
        db.commit()
        print(f"OK_SET_ADMIN {user.id} {user.email}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
