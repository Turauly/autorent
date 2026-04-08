from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.chat_message import ChatMessage
from app.models.user import User
from app.routers.auth import get_current_admin, get_current_user
from app.schemas import ChatMessageCreate, ChatMessageOut, UserOut

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.get("/my", response_model=list[ChatMessageOut])
def get_my_chat(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == current_user.id)
        .order_by(ChatMessage.id.asc())
        .all()
    )


@router.post("/send", response_model=ChatMessageOut, status_code=status.HTTP_201_CREATED)
def send_message(
    payload: ChatMessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_user_id = (
        payload.user_id if current_user.role == "admin" and payload.user_id else current_user.id
    )
    if current_user.role != "admin" and payload.user_id and payload.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    if not db.query(User).filter(User.id == target_user_id).first():
        raise HTTPException(status_code=404, detail="User not found")

    row = ChatMessage(
        user_id=target_user_id,
        sender_role="admin" if current_user.role == "admin" else "user",
        message=payload.message.strip(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/users", response_model=list[UserOut])
def list_chat_users(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    user_ids = (
        db.query(ChatMessage.user_id)
        .group_by(ChatMessage.user_id)
        .order_by(desc(func.max(ChatMessage.id)))
        .all()
    )
    ids = [row[0] for row in user_ids]
    if not ids:
        return []
    users = db.query(User).filter(User.id.in_(ids)).all()
    users_by_id = {u.id: u for u in users}
    return [users_by_id[i] for i in ids if i in users_by_id]


@router.get("/user/{user_id}", response_model=list[ChatMessageOut])
def get_user_chat(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == user_id)
        .order_by(ChatMessage.id.asc())
        .all()
    )
