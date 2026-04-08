from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.car import Car
from app.models.client_request import ClientRequest
from app.models.expense import Expense
from app.models.rental import Rental
from app.models.user import User
from app.routers.auth import get_current_admin
from app.schemas import (
    AdminOverviewOut,
    AdminRentalTimelineItem,
    AdminRentalTimelineResponse,
    AuditLogListResponse,
    CarOut,
    CarServiceUpdate,
    ClientRequestListResponse,
    ClientRequestOut,
    ClientRequestUpdate,
    ExpenseCreate,
    ExpenseListResponse,
    ExpenseOut,
    MessageOut,
    UserBlacklistUpdate,
    UserOut,
)
from app.services.audit_service import log_action

router = APIRouter(prefix="/admin", tags=["Admin"])


def _month_range() -> tuple[date, date]:
    today = date.today()
    month_start = today.replace(day=1)
    next_month = (month_start + timedelta(days=32)).replace(day=1)
    return month_start, next_month


def _serialize_client_request(row: ClientRequest, user: User | None) -> ClientRequestOut:
    return ClientRequestOut(
        id=row.id,
        user_id=row.user_id,
        user_email=user.email if user else None,
        user_full_name=user.full_name if user else None,
        subject=row.subject,
        message=row.message,
        status=row.status,
        admin_comment=row.admin_comment,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    return db.query(User).order_by(desc(User.id)).all()


@router.get("/overview", response_model=AdminOverviewOut)
def get_overview(db: Session = Depends(get_db), _: User = Depends(get_current_admin)):
    month_start, next_month = _month_range()

    total_users = db.query(func.count(User.id)).scalar() or 0
    total_cars = db.query(func.count(Car.id)).scalar() or 0
    active_rentals = db.query(func.count(Rental.id)).filter(Rental.status == "active").scalar() or 0
    completed_rentals = (
        db.query(func.count(Rental.id)).filter(Rental.status == "completed").scalar() or 0
    )

    monthly_revenue = (
        db.query(func.coalesce(func.sum(Rental.total_price), 0.0))
        .filter(
            and_(
                Rental.start_date >= month_start,
                Rental.start_date < next_month,
                Rental.status.in_(["active", "completed"]),
            )
        )
        .scalar()
        or 0.0
    )
    monthly_expenses = (
        db.query(func.coalesce(func.sum(Expense.amount), 0.0))
        .filter(and_(Expense.expense_date >= month_start, Expense.expense_date < next_month))
        .scalar()
        or 0.0
    )
    monthly_profit = monthly_revenue - monthly_expenses

    active_and_completed_count = (
        db.query(func.count(Rental.id)).filter(Rental.status.in_(["active", "completed"])).scalar()
        or 0
    )
    avg_check = (
        round(monthly_revenue / active_and_completed_count, 2)
        if active_and_completed_count
        else 0.0
    )

    return {
        "total_users": total_users,
        "total_cars": total_cars,
        "active_rentals": active_rentals,
        "completed_rentals": completed_rentals,
        "monthly_revenue": round(float(monthly_revenue), 2),
        "monthly_expenses": round(float(monthly_expenses), 2),
        "monthly_profit": round(float(monthly_profit), 2),
        "avg_check": round(float(avg_check), 2),
    }


@router.get("/rental-timeline", response_model=AdminRentalTimelineResponse)
def list_rental_timeline(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
    user_id: int | None = Query(default=None),
    car_id: int | None = Query(default=None),
    status_filter: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=200),
):
    query = (
        db.query(Rental, User, Car)
        .join(User, User.id == Rental.user_id)
        .join(Car, Car.id == Rental.car_id)
    )
    if user_id is not None:
        query = query.filter(Rental.user_id == user_id)
    if car_id is not None:
        query = query.filter(Rental.car_id == car_id)
    if status_filter:
        query = query.filter(Rental.status == status_filter.strip().lower())

    total = query.with_entities(func.count(Rental.id)).scalar() or 0
    rows = query.order_by(desc(Rental.id)).offset((page - 1) * limit).limit(limit).all()

    items = [
        AdminRentalTimelineItem(
            rental_id=rental.id,
            start_date=rental.start_date,
            end_date=rental.end_date,
            total_price=rental.total_price,
            status=rental.status,
            user_id=user.id,
            user_email=user.email,
            user_full_name=user.full_name,
            car_id=car.id,
            car_brand=car.brand,
            car_model=car.model,
            car_category=car.category,
        )
        for rental, user, car in rows
    ]

    return {"items": items, "total": total, "page": page, "limit": limit}


@router.get("/audit-logs", response_model=AuditLogListResponse)
def list_audit_logs(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
    user_id: int | None = Query(default=None),
    action: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=200),
):
    query = db.query(AuditLog)
    if user_id is not None:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)

    total = query.with_entities(func.count(AuditLog.id)).scalar() or 0
    items = query.order_by(desc(AuditLog.id)).offset((page - 1) * limit).limit(limit).all()
    return {"items": items, "total": total, "page": page, "limit": limit}


@router.get("/expenses", response_model=ExpenseListResponse)
def list_expenses(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=200),
):
    query = db.query(Expense)
    total = query.with_entities(func.count(Expense.id)).scalar() or 0
    items = (
        query.order_by(desc(Expense.expense_date), desc(Expense.id))
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return {"items": items, "total": total, "page": page, "limit": limit}


@router.post("/expenses", response_model=ExpenseOut, status_code=status.HTTP_201_CREATED)
def create_expense(
    payload: ExpenseCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    row = Expense(
        title=payload.title.strip(),
        amount=payload.amount,
        category=payload.category.strip().lower(),
        expense_date=payload.expense_date,
        note=payload.note,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    log_action(
        db,
        action="expense_created",
        user_id=current_admin.id,
        entity_type="expense",
        entity_id=row.id,
        details=f"amount={row.amount};category={row.category}",
    )
    return row


@router.get("/client-requests", response_model=ClientRequestListResponse)
def list_client_requests(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
    status_filter: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=200),
):
    query = db.query(ClientRequest)
    if status_filter:
        query = query.filter(ClientRequest.status == status_filter.strip().lower())

    total = query.with_entities(func.count(ClientRequest.id)).scalar() or 0
    rows = query.order_by(desc(ClientRequest.id)).offset((page - 1) * limit).limit(limit).all()

    user_ids = [row.user_id for row in rows]
    users = db.query(User).filter(User.id.in_(user_ids)).all() if user_ids else []
    users_by_id = {user.id: user for user in users}

    items = [_serialize_client_request(row, users_by_id.get(row.user_id)) for row in rows]
    return {"items": items, "total": total, "page": page, "limit": limit}


@router.patch("/client-requests/{request_id}", response_model=ClientRequestOut)
def update_client_request(
    request_id: int,
    payload: ClientRequestUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    row = db.query(ClientRequest).filter(ClientRequest.id == request_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Client request not found")

    if payload.status is not None:
        row.status = payload.status
    if payload.admin_comment is not None:
        row.admin_comment = payload.admin_comment.strip() if payload.admin_comment else None

    db.commit()
    db.refresh(row)
    user = db.query(User).filter(User.id == row.user_id).first()

    log_action(
        db,
        action="client_request_updated",
        user_id=current_admin.id,
        entity_type="client_request",
        entity_id=row.id,
        details=f"status={row.status}",
    )
    return _serialize_client_request(row, user)


@router.post("/transfer/{user_id}", response_model=MessageOut, status_code=status.HTTP_200_OK)
def transfer_admin_role(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    if not target_user.is_verified:
        raise HTTPException(status_code=400, detail="Target user is not verified")

    db.query(User).filter(User.role == "admin").update({"role": "user"})
    target_user.role = "admin"
    db.commit()

    log_action(
        db,
        action="admin_transferred",
        user_id=current_admin.id,
        entity_type="user",
        entity_id=target_user.id,
        details=f"new_admin={target_user.email}",
    )
    return {"message": f"Admin role transferred to user_id={target_user.id}"}


@router.patch("/users/{user_id}/blacklist", response_model=UserOut)
def blacklist_user(
    user_id: int,
    payload: UserBlacklistUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    if target_user.id == current_admin.id:
        raise HTTPException(status_code=400, detail="Cannot blacklist yourself")

    target_user.is_blacklisted = payload.is_blacklisted
    db.commit()
    db.refresh(target_user)

    log_action(
        db,
        action="user_blacklist_updated",
        user_id=current_admin.id,
        entity_type="user",
        entity_id=target_user.id,
        details=f"is_blacklisted={target_user.is_blacklisted};reason={payload.reason or ''}",
    )
    return target_user


@router.patch("/cars/{car_id}/service", response_model=CarOut)
def update_car_service(
    car_id: int,
    payload: CarServiceUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    row = db.query(Car).filter(Car.id == car_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Car not found")

    row.next_service_date = payload.next_service_date
    row.service_note = payload.service_note.strip() if payload.service_note else None
    db.commit()
    db.refresh(row)

    log_action(
        db,
        action="car_service_updated",
        user_id=current_admin.id,
        entity_type="car",
        entity_id=row.id,
        details=f"next_service_date={row.next_service_date}",
    )
    return row
