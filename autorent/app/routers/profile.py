from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.client_request import ClientRequest
from app.models.user import User
from app.models.user_document import UserDocument
from app.routers.auth import get_current_user
from app.schemas import ClientRequestCreate, ClientRequestOut, UserDocumentCreate, UserDocumentOut
from app.services.audit_service import log_action

router = APIRouter(prefix="/profile", tags=["Profile"])
UPLOAD_DIR = Path("uploads/documents")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/documents", response_model=list[UserDocumentOut])
def list_my_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(UserDocument).filter(UserDocument.user_id == current_user.id).all()


@router.post("/documents", response_model=UserDocumentOut, status_code=status.HTTP_201_CREATED)
def add_my_document(
    payload: UserDocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = UserDocument(
        user_id=current_user.id,
        document_type=payload.document_type,
        document_number=payload.document_number,
        file_url=payload.file_url,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.post(
    "/documents/upload", response_model=UserDocumentOut, status_code=status.HTTP_201_CREATED
)
def upload_my_document(
    document_type: str = Form(...),
    document_number: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_suffix = Path(file.filename).suffix
    generated_name = f"{current_user.id}_{uuid4().hex}{file_suffix}"
    file_path = UPLOAD_DIR / generated_name
    with file_path.open("wb") as out:
        out.write(file.file.read())

    row = UserDocument(
        user_id=current_user.id,
        document_type=document_type,
        document_number=document_number,
        file_url=str(file_path).replace("\\", "/"),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/requests", response_model=list[ClientRequestOut])
def list_my_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(ClientRequest)
        .filter(ClientRequest.user_id == current_user.id)
        .order_by(ClientRequest.id.desc())
        .all()
    )
    return [
        ClientRequestOut(
            id=row.id,
            user_id=row.user_id,
            user_email=current_user.email,
            user_full_name=current_user.full_name,
            subject=row.subject,
            message=row.message,
            status=row.status,
            admin_comment=row.admin_comment,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )
        for row in rows
    ]


@router.post("/requests", response_model=ClientRequestOut, status_code=status.HTTP_201_CREATED)
def create_my_request(
    payload: ClientRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = ClientRequest(
        user_id=current_user.id,
        subject=payload.subject.strip(),
        message=payload.message.strip(),
        status="open",
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    log_action(
        db,
        action="client_request_created",
        user_id=current_user.id,
        entity_type="client_request",
        entity_id=row.id,
        details=row.subject,
    )
    return ClientRequestOut(
        id=row.id,
        user_id=row.user_id,
        user_email=current_user.email,
        user_full_name=current_user.full_name,
        subject=row.subject,
        message=row.message,
        status=row.status,
        admin_comment=row.admin_comment,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
