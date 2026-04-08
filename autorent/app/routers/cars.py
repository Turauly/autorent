from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import asc, desc, func
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.car import Car
from app.models.car_photo import CarPhoto
from app.models.user import User
from app.routers.auth import get_current_admin
from app.schemas import CarCreate, CarListResponse, CarOut, CarUpdate
from app.services.audit_service import log_action

router = APIRouter(prefix="/cars", tags=["Cars"])


@router.get("/", response_model=CarListResponse)
def get_cars(
    db: Session = Depends(get_db),
    q: str | None = Query(default=None, description="Search by brand/model"),
    category: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    seats_min: int | None = Query(default=None, ge=2),
    has_ac: bool | None = Query(default=None),
    has_gps: bool | None = Query(default=None),
    has_bluetooth: bool | None = Query(default=None),
    is_electric: bool | None = Query(default=None),
    sort_by: Literal["price_per_day", "year", "brand"] = "price_per_day",
    sort_order: Literal["asc", "desc"] = "asc",
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
):
    query = db.query(Car).options(joinedload(Car.photos))

    if q:
        like_value = f"%{q.strip()}%"
        query = query.filter((Car.brand.ilike(like_value)) | (Car.model.ilike(like_value)))

    if category:
        query = query.filter(Car.category == category.lower())

    if status_filter:
        query = query.filter(Car.status == status_filter)

    if min_price is not None:
        query = query.filter(Car.price_per_day >= min_price)

    if max_price is not None:
        query = query.filter(Car.price_per_day <= max_price)

    if seats_min is not None:
        query = query.filter(Car.seats >= seats_min)

    if has_ac is not None:
        query = query.filter(Car.has_ac == has_ac)

    if has_gps is not None:
        query = query.filter(Car.has_gps == has_gps)

    if has_bluetooth is not None:
        query = query.filter(Car.has_bluetooth == has_bluetooth)

    if is_electric is not None:
        query = query.filter(Car.is_electric == is_electric)

    sort_column = getattr(Car, sort_by)
    order_expression = asc(sort_column) if sort_order == "asc" else desc(sort_column)
    query = query.order_by(order_expression)

    total = query.with_entities(func.count(Car.id)).scalar() or 0
    items = query.offset((page - 1) * limit).limit(limit).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
    }


@router.get("/{car_id}", response_model=CarOut)
def get_car(car_id: int, db: Session = Depends(get_db)):
    car = db.query(Car).options(joinedload(Car.photos)).filter(Car.id == car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    return car


@router.post("/", response_model=CarOut, status_code=status.HTTP_201_CREATED)
def create_car(
    car: CarCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    payload = car.model_dump(exclude={"image_urls"})
    db_car = Car(**payload)
    db.add(db_car)
    db.flush()

    for image_url in car.image_urls:
        db.add(CarPhoto(car_id=db_car.id, url=image_url))

    db.commit()
    db.refresh(db_car)

    log_action(
        db,
        action="car_created",
        user_id=current_admin.id,
        entity_type="car",
        entity_id=db_car.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return db.query(Car).options(joinedload(Car.photos)).filter(Car.id == db_car.id).first()


@router.put("/{car_id}", response_model=CarOut)
def update_car(
    car_id: int,
    car_update: CarUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    db_car = db.query(Car).filter(Car.id == car_id).first()
    if not db_car:
        raise HTTPException(status_code=404, detail="Car not found")

    values = car_update.model_dump(exclude_unset=True, exclude={"image_urls"})
    for key, value in values.items():
        setattr(db_car, key, value)

    if car_update.image_urls is not None:
        db.query(CarPhoto).filter(CarPhoto.car_id == car_id).delete()
        for image_url in car_update.image_urls:
            db.add(CarPhoto(car_id=car_id, url=image_url))

    db.commit()

    log_action(
        db,
        action="car_updated",
        user_id=current_admin.id,
        entity_type="car",
        entity_id=car_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return db.query(Car).options(joinedload(Car.photos)).filter(Car.id == car_id).first()


@router.delete("/{car_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_car(
    car_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    db_car = db.query(Car).filter(Car.id == car_id).first()
    if not db_car:
        raise HTTPException(status_code=404, detail="Car not found")

    db.delete(db_car)
    db.commit()

    log_action(
        db,
        action="car_deleted",
        user_id=current_admin.id,
        entity_type="car",
        entity_id=car_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return None
