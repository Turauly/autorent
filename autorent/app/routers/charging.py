from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import asc, desc, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.car import Car
from app.models.charging_booking import ChargingBooking
from app.models.charging_notification import ChargingNotification
from app.models.charging_review import ChargingReview
from app.models.charging_session import ChargingSession
from app.models.charging_station import ChargingStation
from app.models.rental import Rental
from app.models.user import User
from app.routers.auth import get_current_admin, get_current_user
from app.schemas import (
    ChargingAnalyticsOut,
    ChargingBookingCreate,
    ChargingBookingListResponse,
    ChargingBookingOut,
    ChargingBookingStatusUpdate,
    ChargingNotificationListResponse,
    ChargingNotificationOut,
    ChargingNotificationReadUpdate,
    ChargingReviewCreate,
    ChargingReviewListResponse,
    ChargingReviewOut,
    ChargingSessionCreate,
    ChargingSessionListResponse,
    ChargingSessionOut,
    ChargingStationAvailabilityUpdate,
    ChargingStationCreate,
    ChargingStationListResponse,
    ChargingStationOut,
)

router = APIRouter(prefix="/charging-stations", tags=["Charging"])


def _station_rating_map(db: Session) -> dict[int, tuple[float, int]]:
    rows = (
        db.query(
            ChargingReview.station_id,
            func.coalesce(func.avg(ChargingReview.rating), 0.0),
            func.count(ChargingReview.id),
        )
        .group_by(ChargingReview.station_id)
        .all()
    )
    return {
        station_id: (round(float(avg_rating or 0.0), 2), int(review_count or 0))
        for station_id, avg_rating, review_count in rows
    }


def _serialize_station(
    row: ChargingStation,
    rating_map: dict[int, tuple[float, int]],
) -> ChargingStationOut:
    avg_rating, review_count = rating_map.get(row.id, (0.0, 0))
    return ChargingStationOut(
        id=row.id,
        name=row.name,
        city=row.city,
        address=row.address,
        charger_type=row.charger_type,
        connector_types=row.connector_types,
        slot_count=row.slot_count,
        power_kw=row.power_kw,
        price_per_kwh=row.price_per_kwh,
        latitude=row.latitude,
        longitude=row.longitude,
        is_available=row.is_available,
        note=row.note,
        avg_rating=avg_rating,
        review_count=review_count,
    )


def _serialize_session(
    row: ChargingSession,
    station: ChargingStation | None,
    car: Car | None,
) -> ChargingSessionOut:
    return ChargingSessionOut(
        id=row.id,
        rental_id=row.rental_id,
        car_id=row.car_id,
        station_id=row.station_id,
        charged_at=row.charged_at,
        kwh_amount=row.kwh_amount,
        price_per_kwh=row.price_per_kwh,
        total_cost=row.total_cost,
        duration_minutes=row.duration_minutes,
        battery_percent_start=row.battery_percent_start,
        battery_percent_end=row.battery_percent_end,
        payment_status=row.payment_status,
        note=row.note,
        station_name=station.name if station else None,
        station_city=station.city if station else None,
        station_address=station.address if station else None,
        car_brand=car.brand if car else None,
        car_model=car.model if car else None,
    )


def _serialize_booking(row: ChargingBooking, station: ChargingStation | None) -> ChargingBookingOut:
    return ChargingBookingOut(
        id=row.id,
        user_id=row.user_id,
        station_id=row.station_id,
        booking_date=row.booking_date,
        start_time=row.start_time,
        end_time=row.end_time,
        status=row.status,
        note=row.note,
        created_at=row.created_at,
        station_name=station.name if station else None,
        station_city=station.city if station else None,
    )


def _serialize_review(
    row: ChargingReview,
    user: User | None,
    station: ChargingStation | None,
) -> ChargingReviewOut:
    return ChargingReviewOut(
        id=row.id,
        user_id=row.user_id,
        station_id=row.station_id,
        rating=row.rating,
        comment=row.comment,
        created_at=row.created_at,
        user_email=user.email if user else None,
        station_name=station.name if station else None,
    )


def _serialize_notification(row: ChargingNotification) -> ChargingNotificationOut:
    return ChargingNotificationOut(
        id=row.id,
        user_id=row.user_id,
        station_id=row.station_id,
        title=row.title,
        message=row.message,
        is_read=row.is_read,
        created_at=row.created_at,
    )


def _create_notification(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    station_id: int | None = None,
) -> None:
    db.add(
        ChargingNotification(
            user_id=user_id,
            station_id=station_id,
            title=title,
            message=message,
            is_read=False,
        )
    )


@router.get("/", response_model=ChargingStationListResponse)
def list_charging_stations(
    db: Session = Depends(get_db),
    city: str | None = Query(default=None),
    connector_type: str | None = Query(default=None),
    available_only: bool = Query(default=False),
    sort_by: str = Query(default="price_per_kwh"),
    sort_order: str = Query(default="asc"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    query = db.query(ChargingStation)
    if city:
        query = query.filter(ChargingStation.city.ilike(f"%{city.strip()}%"))
    if connector_type:
        query = query.filter(ChargingStation.connector_types.ilike(f"%{connector_type.strip()}%"))
    if available_only:
        query = query.filter(ChargingStation.is_available.is_(True))

    sortable = {
        "price_per_kwh": ChargingStation.price_per_kwh,
        "power_kw": ChargingStation.power_kw,
        "city": ChargingStation.city,
        "name": ChargingStation.name,
    }
    sort_column = sortable.get(sort_by, ChargingStation.price_per_kwh)
    order_exp = asc(sort_column) if sort_order == "asc" else desc(sort_column)

    total = query.with_entities(func.count(ChargingStation.id)).scalar() or 0
    rows = query.order_by(order_exp, ChargingStation.name.asc()).offset((page - 1) * limit).limit(limit).all()
    rating_map = _station_rating_map(db)
    items = [_serialize_station(row, rating_map) for row in rows]
    return {"items": items, "total": total, "page": page, "limit": limit}


@router.post("/", response_model=ChargingStationOut, status_code=status.HTTP_201_CREATED)
def create_charging_station(
    payload: ChargingStationCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    row = ChargingStation(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return _serialize_station(row, {})


@router.patch("/{station_id}/availability", response_model=ChargingStationOut)
def update_station_availability(
    station_id: int,
    payload: ChargingStationAvailabilityUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
):
    row = db.query(ChargingStation).filter(ChargingStation.id == station_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Charging station not found")
    row.is_available = payload.is_available
    db.commit()
    db.refresh(row)
    return _serialize_station(row, _station_rating_map(db))


@router.post("/bookings", response_model=ChargingBookingOut, status_code=status.HTTP_201_CREATED)
def create_booking(
    payload: ChargingBookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    station = db.query(ChargingStation).filter(ChargingStation.id == payload.station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Charging station not found")
    if not station.is_available:
        raise HTTPException(status_code=400, detail="Charging station is not available")

    overlap = (
        db.query(ChargingBooking)
        .filter(
            ChargingBooking.station_id == payload.station_id,
            ChargingBooking.booking_date == payload.booking_date,
            ChargingBooking.status == "booked",
            ChargingBooking.start_time < payload.end_time,
            ChargingBooking.end_time > payload.start_time,
        )
        .first()
    )
    if overlap:
        raise HTTPException(status_code=400, detail="Charging station already booked for this time")

    row = ChargingBooking(
        user_id=current_user.id,
        station_id=payload.station_id,
        booking_date=payload.booking_date,
        start_time=payload.start_time,
        end_time=payload.end_time,
        status="booked",
        note=payload.note,
    )
    db.add(row)
    _create_notification(
        db,
        user_id=current_user.id,
        station_id=station.id,
        title="Charging booking confirmed",
        message=f"{station.name}: {payload.booking_date} {payload.start_time}-{payload.end_time}",
    )
    db.commit()
    db.refresh(row)
    return _serialize_booking(row, station)


@router.get("/bookings/my", response_model=ChargingBookingListResponse)
def list_my_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    query = (
        db.query(ChargingBooking, ChargingStation)
        .join(ChargingStation, ChargingStation.id == ChargingBooking.station_id)
        .filter(ChargingBooking.user_id == current_user.id)
    )
    total = query.with_entities(func.count(ChargingBooking.id)).scalar() or 0
    rows = query.order_by(desc(ChargingBooking.booking_date), desc(ChargingBooking.id)).offset((page - 1) * limit).limit(limit).all()
    items = [_serialize_booking(booking, station) for booking, station in rows]
    return {"items": items, "total": total, "page": page, "limit": limit}


@router.get("/bookings", response_model=ChargingBookingListResponse)
def list_all_bookings(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    query = (
        db.query(ChargingBooking, ChargingStation)
        .join(ChargingStation, ChargingStation.id == ChargingBooking.station_id)
    )
    total = query.with_entities(func.count(ChargingBooking.id)).scalar() or 0
    rows = query.order_by(desc(ChargingBooking.booking_date), desc(ChargingBooking.id)).offset((page - 1) * limit).limit(limit).all()
    items = [_serialize_booking(booking, station) for booking, station in rows]
    return {"items": items, "total": total, "page": page, "limit": limit}


@router.patch("/bookings/{booking_id}", response_model=ChargingBookingOut)
def update_booking_status(
    booking_id: int,
    payload: ChargingBookingStatusUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    row = db.query(ChargingBooking).filter(ChargingBooking.id == booking_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Charging booking not found")
    station = db.query(ChargingStation).filter(ChargingStation.id == row.station_id).first()
    row.status = payload.status
    title = "Booking updated"
    message = f"{station.name if station else 'Station'}: status {payload.status}"
    if payload.status == "completed":
        title = "Booking approved"
    elif payload.status == "canceled":
        title = "Booking canceled"
    _create_notification(
        db,
        user_id=row.user_id,
        station_id=row.station_id,
        title=title,
        message=message,
    )
    db.commit()
    db.refresh(row)
    return _serialize_booking(row, station)


@router.post("/reviews", response_model=ChargingReviewOut, status_code=status.HTTP_201_CREATED)
def create_review(
    payload: ChargingReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    station = db.query(ChargingStation).filter(ChargingStation.id == payload.station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Charging station not found")
    row = ChargingReview(
        user_id=current_user.id,
        station_id=payload.station_id,
        rating=payload.rating,
        comment=payload.comment,
    )
    db.add(row)
    _create_notification(
        db,
        user_id=current_user.id,
        station_id=station.id,
        title="Review saved",
        message=f"{station.name}: {payload.rating}/5",
    )
    db.commit()
    db.refresh(row)
    return _serialize_review(row, current_user, station)


@router.get("/reviews", response_model=ChargingReviewListResponse)
def list_reviews(
    db: Session = Depends(get_db),
    station_id: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    query = (
        db.query(ChargingReview, User, ChargingStation)
        .join(User, User.id == ChargingReview.user_id)
        .join(ChargingStation, ChargingStation.id == ChargingReview.station_id)
    )
    if station_id is not None:
        query = query.filter(ChargingReview.station_id == station_id)
    total = query.with_entities(func.count(ChargingReview.id)).scalar() or 0
    rows = query.order_by(desc(ChargingReview.id)).offset((page - 1) * limit).limit(limit).all()
    items = [_serialize_review(review, user, station) for review, user, station in rows]
    return {"items": items, "total": total, "page": page, "limit": limit}


@router.post("/sessions", response_model=ChargingSessionOut, status_code=status.HTTP_201_CREATED)
def create_charging_session(
    payload: ChargingSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rental = db.query(Rental).filter(Rental.id == payload.rental_id).first()
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")
    if current_user.role != "admin" and rental.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    car = db.query(Car).filter(Car.id == rental.car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    if not car.is_electric:
        raise HTTPException(status_code=400, detail="Charging sessions are only available for electric cars")

    station = db.query(ChargingStation).filter(ChargingStation.id == payload.station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Charging station not found")

    price_per_kwh = payload.price_per_kwh or station.price_per_kwh
    total_cost = round(payload.kwh_amount * price_per_kwh, 2)
    row = ChargingSession(
        rental_id=rental.id,
        car_id=rental.car_id,
        station_id=station.id,
        charged_at=payload.charged_at,
        kwh_amount=payload.kwh_amount,
        price_per_kwh=price_per_kwh,
        total_cost=total_cost,
        duration_minutes=payload.duration_minutes,
        battery_percent_start=payload.battery_percent_start,
        battery_percent_end=payload.battery_percent_end,
        payment_status=payload.payment_status,
        note=payload.note,
    )
    db.add(row)
    if payload.battery_percent_end is not None and payload.battery_percent_end >= 80:
        _create_notification(
            db,
            user_id=rental.user_id,
            station_id=station.id,
            title="Charging complete",
            message=f"{station.name}: battery reached {payload.battery_percent_end}%",
        )
    db.commit()
    db.refresh(row)
    return _serialize_session(row, station, car)


@router.get("/sessions/my", response_model=ChargingSessionListResponse)
def list_my_charging_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    query = (
        db.query(ChargingSession, ChargingStation, Car, Rental)
        .join(ChargingStation, ChargingStation.id == ChargingSession.station_id)
        .join(Car, Car.id == ChargingSession.car_id)
        .join(Rental, Rental.id == ChargingSession.rental_id)
        .filter(Rental.user_id == current_user.id)
    )
    total = query.with_entities(func.count(ChargingSession.id)).scalar() or 0
    rows = query.order_by(desc(ChargingSession.charged_at), desc(ChargingSession.id)).offset((page - 1) * limit).limit(limit).all()
    items = [_serialize_session(session, station, car) for session, station, car, _ in rows]
    return {"items": items, "total": total, "page": page, "limit": limit}


@router.get("/sessions", response_model=ChargingSessionListResponse)
def list_all_charging_sessions(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_admin),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    query = (
        db.query(ChargingSession, ChargingStation, Car)
        .join(ChargingStation, ChargingStation.id == ChargingSession.station_id)
        .join(Car, Car.id == ChargingSession.car_id)
    )
    total = query.with_entities(func.count(ChargingSession.id)).scalar() or 0
    rows = query.order_by(desc(ChargingSession.charged_at), desc(ChargingSession.id)).offset((page - 1) * limit).limit(limit).all()
    items = [_serialize_session(session, station, car) for session, station, car in rows]
    return {"items": items, "total": total, "page": page, "limit": limit}


@router.get("/analytics/my", response_model=ChargingAnalyticsOut)
def my_charging_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rows = (
        db.query(ChargingSession, ChargingStation, Rental)
        .join(ChargingStation, ChargingStation.id == ChargingSession.station_id)
        .join(Rental, Rental.id == ChargingSession.rental_id)
        .filter(Rental.user_id == current_user.id)
        .all()
    )
    total_sessions = len(rows)
    total_kwh = round(sum(float(row[0].kwh_amount or 0) for row in rows), 2)
    total_cost = round(sum(float(row[0].total_cost or 0) for row in rows), 2)
    avg_session_cost = round(total_cost / total_sessions, 2) if total_sessions else 0.0
    fuel_saved_liters = round(total_kwh * 0.12, 2)
    co2_saved_kg = round(fuel_saved_liters * 2.31, 2)
    grouped: dict[str, int] = {}
    for _, station, _ in rows:
        grouped[station.name] = grouped.get(station.name, 0) + 1
    top_station_name = max(grouped, key=grouped.get) if grouped else None
    top_station_visits = grouped.get(top_station_name, 0) if top_station_name else 0
    return {
        "total_sessions": total_sessions,
        "total_kwh": total_kwh,
        "total_cost": total_cost,
        "avg_session_cost": avg_session_cost,
        "fuel_saved_liters": fuel_saved_liters,
        "co2_saved_kg": co2_saved_kg,
        "top_station_name": top_station_name,
        "top_station_visits": top_station_visits,
    }


@router.get("/notifications/my", response_model=ChargingNotificationListResponse)
def list_my_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
):
    query = db.query(ChargingNotification).filter(ChargingNotification.user_id == current_user.id)
    total = query.with_entities(func.count(ChargingNotification.id)).scalar() or 0
    rows = query.order_by(desc(ChargingNotification.id)).offset((page - 1) * limit).limit(limit).all()
    return {"items": [_serialize_notification(row) for row in rows], "total": total, "page": page, "limit": limit}


@router.patch("/notifications/{notification_id}", response_model=ChargingNotificationOut)
def mark_notification(
    notification_id: int,
    payload: ChargingNotificationReadUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = (
        db.query(ChargingNotification)
        .filter(ChargingNotification.id == notification_id, ChargingNotification.user_id == current_user.id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Notification not found")
    row.is_read = payload.is_read
    db.commit()
    db.refresh(row)
    return _serialize_notification(row)
