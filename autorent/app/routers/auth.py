import random
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import ALGORITHM, SECRET_KEY
from app.core.security import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models.email_verification import EmailVerificationCode
from app.models.user import User
from app.schemas import (
    MessageOut,
    RegisterCodeRequest,
    RegisterConfirmRequest,
    Token,
    UserOut,
)
from app.services.audit_service import log_action
from app.services.email_service import send_verification_code

router = APIRouter(prefix="/auth", tags=["Auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@router.post("/register/request-code", response_model=MessageOut)
def request_register_code(payload: RegisterCodeRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    code = f"{random.randint(100000, 999999)}"
    try:
        send_verification_code(payload.email, code)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    row = EmailVerificationCode(
        email=payload.email,
        code=code,
        expires_at=datetime.now(UTC) + timedelta(minutes=10),
        used=False,
    )
    db.add(row)
    db.commit()
    log_action(db, action="register_code_requested", details=f"email={payload.email}")
    return {"message": "Verification code sent"}


@router.post("/register/confirm", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_confirm(
    payload: RegisterConfirmRequest, request: Request, db: Session = Depends(get_db)
):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    code_row = (
        db.query(EmailVerificationCode)
        .filter(
            EmailVerificationCode.email == payload.email,
            EmailVerificationCode.code == payload.code,
            EmailVerificationCode.used.is_(False),
        )
        .order_by(EmailVerificationCode.id.desc())
        .first()
    )

    if not code_row:
        raise HTTPException(status_code=400, detail="Invalid verification code")

    now = datetime.now(UTC)
    expires_at = code_row.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at < now:
        raise HTTPException(status_code=400, detail="Verification code expired")

    has_admin = db.query(User).filter(User.role == "admin").first() is not None
    role = "user" if has_admin else "admin"

    new_user = User(
        full_name=payload.full_name,
        phone=payload.phone,
        email=payload.email,
        password_hash=hash_password(payload.password),
        role=role,
        is_verified=True,
    )

    code_row.used = True
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    log_action(
        db,
        action="register_confirmed",
        user_id=new_user.id,
        entity_type="user",
        entity_id=new_user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return new_user


@router.post("/login", response_model=Token)
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.is_blacklisted:
        raise HTTPException(status_code=403, detail="Account is blacklisted")

    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Email is not verified")

    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    log_action(
        db,
        action="login_success",
        user_id=user.id,
        entity_type="user",
        entity_id=user.id,
        ip_address=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout", response_model=MessageOut)
def logout():
    return {"message": "Logged out successfully"}


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    if user.is_blacklisted:
        raise HTTPException(status_code=403, detail="Account is blacklisted")

    return user


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
