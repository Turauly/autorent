from datetime import date
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import asc, desc, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.car import Car
from app.models.rental import Rental
from app.models.user import User
from app.models.waitlist_entry import WaitlistEntry
from app.routers.auth import get_current_admin, get_current_user
from app.schemas import (
    MessageOut,
    RentalCreate,
    RentalListResponse,
    RentalOut,
    WaitlistCreate,
    WaitlistOut,
)
from app.services.audit_service import log_action

router = APIRouter(prefix="/rentals", tags=["Rentals"])


def calculate_total_price(car: Car, start_date: date, end_date: date) -> float:
    days = (end_date - start_date).days
    if days <= 0:
        raise HTTPException(status_code=400, detail="End date must be after start date")
    return days * car.price_per_day


def get_price_variant_for_user(user: User) -> tuple[str, float]:
    # Simple deterministic A/B split for demo purposes.
    if user.id % 2 == 0:
        return "B", 0.95
    return "A", 1.0


@router.post("/", response_model=RentalOut, status_code=status.HTTP_201_CREATED)
def create_rental(
    rental: RentalCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.is_blacklisted:
        raise HTTPException(status_code=403, detail="Blacklisted users cannot create rentals")

    car = db.query(Car).filter(Car.id == rental.car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    if car.status != "available":
        raise HTTPException(status_code=400, detail="Car is not available")

    existing_rental = (
        db.query(Rental)
        .filter(
            Rental.car_id == rental.car_id,
            Rental.status == "active",
            Rental.start_date <= rental.end_date,
            Rental.end_date >= rental.start_date,
        )
        .first()
    )
    if existing_rental:
        raise HTTPException(status_code=400, detail="Car already rented for these dates")

    variant, multiplier = get_price_variant_for_user(current_user)
    total_price = round(
        calculate_total_price(car, rental.start_date, rental.end_date) * multiplier, 2
    )
    db_rental = Rental(
        user_id=current_user.id,
        car_id=rental.car_id,
        start_date=rental.start_date,
        end_date=rental.end_date,
        total_price=total_price,
        status="active",
        price_variant=variant,
    )

    car.status = "rented"
    db.add(db_rental)
    db.commit()
    db.refresh(db_rental)

    log_action(
        db,
        action="rental_created",
        user_id=current_user.id,
        entity_type="rental",
        entity_id=db_rental.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return db_rental


@router.post("/waitlist", response_model=WaitlistOut, status_code=status.HTTP_201_CREATED)
def create_waitlist_entry(
    payload: WaitlistCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.is_blacklisted:
        raise HTTPException(status_code=403, detail="Blacklisted users cannot join waitlist")

    car = db.query(Car).filter(Car.id == payload.car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    row = WaitlistEntry(
        user_id=current_user.id,
        car_id=payload.car_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        status="pending",
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    log_action(
        db,
        action="waitlist_created",
        user_id=current_user.id,
        entity_type="waitlist_entry",
        entity_id=row.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return row


@router.get("/waitlist/my", response_model=list[WaitlistOut])
def list_my_waitlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(WaitlistEntry)
        .filter(WaitlistEntry.user_id == current_user.id)
        .order_by(desc(WaitlistEntry.id))
        .all()
    )


@router.get("/my", response_model=RentalListResponse)
def get_my_rentals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
):
    query = db.query(Rental).filter(Rental.user_id == current_user.id)
    total = query.with_entities(func.count(Rental.id)).scalar() or 0
    items = query.order_by(desc(Rental.id)).offset((page - 1) * limit).limit(limit).all()

    return {"items": items, "total": total, "page": page, "limit": limit}


@router.get("/", response_model=RentalListResponse)
def get_all_rentals(
    db: Session = Depends(get_db),
    _: object = Depends(get_current_admin),
    sort_order: Literal["asc", "desc"] = "desc",
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
):
    query = db.query(Rental)
    total = query.with_entities(func.count(Rental.id)).scalar() or 0
    order_exp = asc(Rental.id) if sort_order == "asc" else desc(Rental.id)
    items = query.order_by(order_exp).offset((page - 1) * limit).limit(limit).all()

    return {"items": items, "total": total, "page": page, "limit": limit}


@router.patch("/{rental_id}/complete", response_model=MessageOut)
def complete_rental(
    rental_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rental = db.query(Rental).filter(Rental.id == rental_id).first()
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")

    if current_user.role != "admin" and rental.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    if rental.status != "active":
        raise HTTPException(status_code=400, detail="Rental is not active")

    rental.status = "completed"
    car = db.query(Car).filter(Car.id == rental.car_id).first()
    if car:
        car.status = "available"

    renter = db.query(User).filter(User.id == rental.user_id).first()
    if renter:
        gained_points = max(1, int((rental.total_price or 0) // 10000))
        renter.loyalty_points = (renter.loyalty_points or 0) + gained_points

    db.commit()

    log_action(
        db,
        action="rental_completed",
        user_id=current_user.id,
        entity_type="rental",
        entity_id=rental.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return {"message": "Rental completed successfully"}
