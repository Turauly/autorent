import logging
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text

from app.core.config import CORS_ORIGINS
from app.database import Base, SessionLocal, engine
from app.models import (  # noqa: F401
    audit_log,
    car,
    car_photo,
    charging_booking,
    charging_notification,
    charging_review,
    charging_session,
    charging_station,
    chat_message,
    client_request,
    email_verification,
    expense,
    rental,
    user,
    user_document,
    waitlist_entry,
)
from app.monitoring import record_request, render_metrics
from app.routers import admin, auth, cars, charging, chat, profile, rentals

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("autorent")
Path("uploads/documents").mkdir(parents=True, exist_ok=True)

ALMATY_CHARGING_STATIONS = [
    {
        "name": "Mega Park Charge Hub",
        "city": "Almaty",
        "address": "улица Макатаева 127/1",
        "charger_type": "DC",
        "connector_types": "CCS2, Type 2",
        "slot_count": 6,
        "power_kw": 120,
        "price_per_kwh": 95,
        "latitude": 43.2642,
        "longitude": 76.9285,
        "is_available": True,
        "note": "Орталықтағы жылдам зарядтау станциясы",
    },
    {
        "name": "Dostyk Plaza EV Point",
        "city": "Almaty",
        "address": "микрорайон Самал-2 111",
        "charger_type": "DC",
        "connector_types": "CCS2, CHAdeMO",
        "slot_count": 4,
        "power_kw": 100,
        "price_per_kwh": 105,
        "latitude": 43.2332,
        "longitude": 76.9569,
        "is_available": True,
        "note": "Сауда орталығы жанындағы EV станция",
    },
    {
        "name": "Esentai Mall Charge Zone",
        "city": "Almaty",
        "address": "проспект Аль-Фараби 77/8",
        "charger_type": "AC/DC",
        "connector_types": "CCS2, Type 2, Tesla",
        "slot_count": 8,
        "power_kw": 150,
        "price_per_kwh": 115,
        "latitude": 43.2183,
        "longitude": 76.9277,
        "is_available": True,
        "note": "Премиум локация, жоғары қуатты заряд",
    },
    {
        "name": "Forum Almaty Green Station",
        "city": "Almaty",
        "address": "проспект Сейфуллина 617",
        "charger_type": "AC",
        "connector_types": "Type 2, CCS2",
        "slot_count": 3,
        "power_kw": 80,
        "price_per_kwh": 89,
        "latitude": 43.2402,
        "longitude": 76.9458,
        "is_available": True,
        "note": "Қала ішіндегі күнделікті зарядтауға ыңғайлы",
    },
]

app = FastAPI(
    title="AutoRent API",
    description="Car rental management system",
    version="1.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials="*" not in CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    try:
        Base.metadata.create_all(bind=engine)
        inspector = inspect(engine)
        user_columns = {c["name"] for c in inspector.get_columns("users")}
        if "is_blacklisted" not in user_columns:
            with engine.begin() as conn:
                conn.execute(
                    text("ALTER TABLE users ADD COLUMN is_blacklisted BOOLEAN NOT NULL DEFAULT 0")
                )
            logger.info("Added users.is_blacklisted column")
        if "loyalty_points" not in user_columns:
            with engine.begin() as conn:
                conn.execute(
                    text("ALTER TABLE users ADD COLUMN loyalty_points INTEGER NOT NULL DEFAULT 0")
                )
            logger.info("Added users.loyalty_points column")

        car_columns = {c["name"] for c in inspector.get_columns("cars")}
        with engine.begin() as conn:
            if "next_service_date" not in car_columns:
                conn.execute(text("ALTER TABLE cars ADD COLUMN next_service_date DATE"))
                logger.info("Added cars.next_service_date column")
            if "service_note" not in car_columns:
                conn.execute(text("ALTER TABLE cars ADD COLUMN service_note TEXT"))
                logger.info("Added cars.service_note column")
            if "is_electric" not in car_columns:
                conn.execute(text("ALTER TABLE cars ADD COLUMN is_electric BOOLEAN NOT NULL DEFAULT 0"))
                logger.info("Added cars.is_electric column")
            if "battery_capacity_kwh" not in car_columns:
                conn.execute(text("ALTER TABLE cars ADD COLUMN battery_capacity_kwh FLOAT"))
                logger.info("Added cars.battery_capacity_kwh column")
            if "range_km" not in car_columns:
                conn.execute(text("ALTER TABLE cars ADD COLUMN range_km INTEGER"))
                logger.info("Added cars.range_km column")
            if "charge_port" not in car_columns:
                conn.execute(text("ALTER TABLE cars ADD COLUMN charge_port VARCHAR(30)"))
                logger.info("Added cars.charge_port column")
        charging_station_columns = {c["name"] for c in inspector.get_columns("charging_stations")}
        with engine.begin() as conn:
            if "connector_types" not in charging_station_columns:
                conn.execute(
                    text(
                        "ALTER TABLE charging_stations ADD COLUMN connector_types VARCHAR(120) NOT NULL DEFAULT 'CCS2'"
                    )
                )
                logger.info("Added charging_stations.connector_types column")
            if "slot_count" not in charging_station_columns:
                conn.execute(
                    text(
                        "ALTER TABLE charging_stations ADD COLUMN slot_count INTEGER NOT NULL DEFAULT 2"
                    )
                )
                logger.info("Added charging_stations.slot_count column")

        rental_columns = {c["name"] for c in inspector.get_columns("rentals")}
        if "price_variant" not in rental_columns:
            with engine.begin() as conn:
                conn.execute(
                    text(
                        "ALTER TABLE rentals ADD COLUMN price_variant VARCHAR(10) NOT NULL DEFAULT 'A'"
                    )
                )
            logger.info("Added rentals.price_variant column")

        db = SessionLocal()
        try:
            from app.models.charging_station import ChargingStation

            existing_almaty = (
                db.query(ChargingStation).filter(ChargingStation.city == "Almaty").count()
            )
            if existing_almaty == 0:
                for station in ALMATY_CHARGING_STATIONS:
                    db.add(ChargingStation(**station))
                db.commit()
                logger.info("Seeded Almaty charging stations")
        finally:
            db.close()

        logger.info("Database tables ensured")
    except Exception as exc:  # pragma: no cover
        logger.warning("Database init skipped: %s", exc)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - started) * 1000
    path = request.scope.get("path", request.url.path)
    record_request(request.method, path, response.status_code, duration_ms)
    logger.info(
        "%s %s -> %s (%.2f ms)",
        request.method,
        path,
        response.status_code,
        duration_ms,
    )
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "message": "Validation failed",
            "errors": exc.errors(),
            "path": request.url.path,
        },
    )


app.include_router(auth.router)
app.include_router(cars.router)
app.include_router(rentals.router)
app.include_router(charging.router)
app.include_router(profile.router)
app.include_router(admin.router)
app.include_router(chat.router)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/")
def root():
    return {"message": "AutoRent API is running"}


@app.get("/healthz")
def healthcheck():
    return {"status": "ok"}


@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    return render_metrics()

