
from sqlalchemy.orm import Session

from app.database.models import User
from app.core.security import hash_password, verify_password, create_access_token


def register_user(db: Session, username: str, email: str, password: str):
    existing_username = (
        db.query(User)
        .filter(User.username == username)
        .first()
    )

    if existing_username:
        raise ValueError("Username already exists")

    existing_email = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if existing_email:
        raise ValueError("Email already registered")

    new_user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception:
        db.rollback()
        raise

    return {
        "message": "Registration successful",
        "user": {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
        },
    }

def login_user(db: Session, email: str, password: str):
    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if not user or not verify_password(password, user.password_hash):
        raise ValueError('Invalid email or password')

    access_token = create_access_token(user.id)

    return {
        'access_token': access_token,
        'token_type': 'bearer',
    }
