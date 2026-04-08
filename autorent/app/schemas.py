from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ALLOWED_CAR_STATUSES = {"available", "rented", "service"}
ALLOWED_CAR_CATEGORIES = {"econom", "budget", "comfort", "lux"}
ALLOWED_RENTAL_STATUSES = {"active", "completed", "canceled"}
ALLOWED_REQUEST_STATUSES = {"open", "in_progress", "resolved", "rejected"}
ALLOWED_PAYMENT_STATUSES = {"paid", "pending"}
ALLOWED_BOOKING_STATUSES = {"booked", "completed", "canceled"}


class MessageOut(BaseModel):
    message: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RegisterCodeRequest(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class RegisterConfirmRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    phone: str | None = Field(default=None, max_length=30)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=6, max_length=128)
    code: str = Field(min_length=4, max_length=10)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str | None
    phone: str | None
    email: str
    role: str
    is_verified: bool
    is_blacklisted: bool
    loyalty_points: int
    created_at: datetime


class CarPhotoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str


class CarBase(BaseModel):
    brand: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=100)
    category: str = Field(default="econom")
    year: int = Field(ge=1900, le=2100)
    transmission: str = Field(default="automatic", max_length=30)
    fuel_type: str = Field(default="petrol", max_length=30)
    seats: int = Field(default=5, ge=2, le=12)
    has_ac: bool = True
    has_gps: bool = False
    has_bluetooth: bool = False
    is_electric: bool = False
    battery_capacity_kwh: float | None = Field(default=None, gt=0)
    range_km: int | None = Field(default=None, ge=1)
    charge_port: str | None = Field(default=None, max_length=30)
    price_per_day: float = Field(gt=0)
    status: str = Field(default="available", max_length=20)
    main_image_url: str | None = None
    next_service_date: date | None = None
    service_note: str | None = Field(default=None, max_length=1000)
    image_urls: list[str] = []

    @field_validator("brand", "model", "transmission", "fuel_type")
    @classmethod
    def strip_names(cls, value: str) -> str:
        return value.strip()

    @field_validator("charge_port")
    @classmethod
    def strip_charge_port(cls, value: str | None) -> str | None:
        return value.strip() if value else value

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in ALLOWED_CAR_STATUSES:
            raise ValueError("Invalid car status")
        return normalized

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in ALLOWED_CAR_CATEGORIES:
            raise ValueError("Invalid car category")
        return normalized

    @model_validator(mode="after")
    def validate_electric_fields(self):
        if self.is_electric and (self.battery_capacity_kwh is None or self.range_km is None):
            raise ValueError("Electric car requires battery_capacity_kwh and range_km")
        if not self.is_electric:
            self.battery_capacity_kwh = None
            self.range_km = None
            self.charge_port = None
        return self


class CarCreate(CarBase):
    pass


class CarUpdate(BaseModel):
    brand: str | None = Field(default=None, min_length=1, max_length=100)
    model: str | None = Field(default=None, min_length=1, max_length=100)
    category: str | None = None
    year: int | None = Field(default=None, ge=1900, le=2100)
    transmission: str | None = Field(default=None, max_length=30)
    fuel_type: str | None = Field(default=None, max_length=30)
    seats: int | None = Field(default=None, ge=2, le=12)
    has_ac: bool | None = None
    has_gps: bool | None = None
    has_bluetooth: bool | None = None
    is_electric: bool | None = None
    battery_capacity_kwh: float | None = Field(default=None, gt=0)
    range_km: int | None = Field(default=None, ge=1)
    charge_port: str | None = Field(default=None, max_length=30)
    price_per_day: float | None = Field(default=None, gt=0)
    status: str | None = Field(default=None, max_length=20)
    main_image_url: str | None = None
    next_service_date: date | None = None
    service_note: str | None = Field(default=None, max_length=1000)
    image_urls: list[str] | None = None

    @field_validator("charge_port")
    @classmethod
    def strip_optional_charge_port(cls, value: str | None) -> str | None:
        return value.strip() if value else value


class CarOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    brand: str
    model: str
    category: str
    year: int
    transmission: str
    fuel_type: str
    seats: int
    has_ac: bool
    has_gps: bool
    has_bluetooth: bool
    is_electric: bool
    battery_capacity_kwh: float | None
    range_km: int | None
    charge_port: str | None
    price_per_day: float
    status: str
    main_image_url: str | None
    next_service_date: date | None
    service_note: str | None
    photos: list[CarPhotoOut] = []


class UserBlacklistUpdate(BaseModel):
    is_blacklisted: bool
    reason: str | None = Field(default=None, max_length=300)


class CarServiceUpdate(BaseModel):
    next_service_date: date | None = None
    service_note: str | None = Field(default=None, max_length=1000)


class CarListResponse(BaseModel):
    items: list[CarOut]
    total: int
    page: int
    limit: int


class RentalCreate(BaseModel):
    car_id: int = Field(gt=0)
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


class RentalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    car_id: int
    start_date: date
    end_date: date
    total_price: float
    status: str
    price_variant: str

    @field_validator("status")
    @classmethod
    def validate_rental_status(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in ALLOWED_RENTAL_STATUSES:
            raise ValueError("Invalid rental status")
        return normalized


class RentalListResponse(BaseModel):
    items: list[RentalOut]
    total: int
    page: int
    limit: int


class WaitlistCreate(BaseModel):
    car_id: int = Field(gt=0)
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


class WaitlistOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    car_id: int
    start_date: date
    end_date: date
    status: str
    created_at: datetime


class UserDocumentCreate(BaseModel):
    document_type: str = Field(min_length=2, max_length=50)
    document_number: str = Field(min_length=3, max_length=50)
    file_url: str | None = None


class UserDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    document_type: str
    document_number: str
    file_url: str | None
    uploaded_at: datetime


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None
    action: str
    entity_type: str | None
    entity_id: int | None
    ip_address: str | None
    user_agent: str | None
    details: str | None
    created_at: datetime


class AuditLogListResponse(BaseModel):
    items: list[AuditLogOut]
    total: int
    page: int
    limit: int


class ExpenseCreate(BaseModel):
    title: str = Field(min_length=2, max_length=120)
    amount: float = Field(gt=0)
    category: str = Field(default="operations", min_length=2, max_length=50)
    expense_date: date
    note: str | None = Field(default=None, max_length=500)


class ExpenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    amount: float
    category: str
    expense_date: date
    note: str | None


class ExpenseListResponse(BaseModel):
    items: list[ExpenseOut]
    total: int
    page: int
    limit: int


class ChargingStationBase(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    city: str = Field(min_length=2, max_length=80)
    address: str = Field(min_length=5, max_length=200)
    charger_type: str = Field(default="DC", min_length=2, max_length=30)
    connector_types: str = Field(default="CCS2", min_length=2, max_length=120)
    slot_count: int = Field(default=2, ge=1, le=50)
    power_kw: float = Field(gt=0)
    price_per_kwh: float = Field(gt=0)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    is_available: bool = True
    note: str | None = Field(default=None, max_length=500)

    @field_validator("connector_types")
    @classmethod
    def normalize_connector_types(cls, value: str) -> str:
        parts = [part.strip().upper() for part in value.split(",") if part.strip()]
        return ", ".join(parts)


class ChargingStationCreate(ChargingStationBase):
    pass


class ChargingStationOut(ChargingStationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    avg_rating: float = 0
    review_count: int = 0


class ChargingStationListResponse(BaseModel):
    items: list[ChargingStationOut]
    total: int
    page: int
    limit: int


class ChargingStationAvailabilityUpdate(BaseModel):
    is_available: bool


class ChargingSessionCreate(BaseModel):
    rental_id: int = Field(gt=0)
    station_id: int = Field(gt=0)
    charged_at: date
    kwh_amount: float = Field(gt=0)
    price_per_kwh: float | None = Field(default=None, gt=0)
    duration_minutes: int | None = Field(default=None, ge=1)
    battery_percent_start: int | None = Field(default=None, ge=0, le=100)
    battery_percent_end: int | None = Field(default=None, ge=0, le=100)
    payment_status: str = Field(default="paid")
    note: str | None = Field(default=None, max_length=500)

    @field_validator("payment_status")
    @classmethod
    def validate_payment_status(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in ALLOWED_PAYMENT_STATUSES:
            raise ValueError("Invalid payment status")
        return normalized

    @model_validator(mode="after")
    def validate_charge_progress(self):
        if (
            self.battery_percent_start is not None
            and self.battery_percent_end is not None
            and self.battery_percent_end < self.battery_percent_start
        ):
            raise ValueError("battery_percent_end must be greater than or equal to battery_percent_start")
        return self


class ChargingSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rental_id: int
    car_id: int
    station_id: int
    charged_at: date
    kwh_amount: float
    price_per_kwh: float
    total_cost: float
    duration_minutes: int | None
    battery_percent_start: int | None
    battery_percent_end: int | None
    payment_status: str
    note: str | None
    station_name: str | None = None
    station_city: str | None = None
    station_address: str | None = None
    car_brand: str | None = None
    car_model: str | None = None


class ChargingSessionListResponse(BaseModel):
    items: list[ChargingSessionOut]
    total: int
    page: int
    limit: int


class ChargingBookingCreate(BaseModel):
    station_id: int = Field(gt=0)
    booking_date: date
    start_time: str = Field(min_length=5, max_length=5)
    end_time: str = Field(min_length=5, max_length=5)
    note: str | None = Field(default=None, max_length=300)

    @model_validator(mode="after")
    def validate_time_range(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class ChargingBookingOut(BaseModel):
    id: int
    user_id: int
    station_id: int
    booking_date: date
    start_time: str
    end_time: str
    status: str
    note: str | None
    created_at: str
    station_name: str | None = None
    station_city: str | None = None


class ChargingBookingListResponse(BaseModel):
    items: list[ChargingBookingOut]
    total: int
    page: int
    limit: int


class ChargingBookingStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_booking_status(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in ALLOWED_BOOKING_STATUSES:
            raise ValueError("Invalid booking status")
        return normalized


class ChargingReviewCreate(BaseModel):
    station_id: int = Field(gt=0)
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=500)


class ChargingReviewOut(BaseModel):
    id: int
    user_id: int
    station_id: int
    rating: int
    comment: str | None
    created_at: str
    user_email: str | None = None
    station_name: str | None = None


class ChargingReviewListResponse(BaseModel):
    items: list[ChargingReviewOut]
    total: int
    page: int
    limit: int


class ChargingNotificationOut(BaseModel):
    id: int
    user_id: int
    station_id: int | None
    title: str
    message: str
    is_read: bool
    created_at: str


class ChargingNotificationListResponse(BaseModel):
    items: list[ChargingNotificationOut]
    total: int
    page: int
    limit: int


class ChargingNotificationReadUpdate(BaseModel):
    is_read: bool


class ChargingAnalyticsOut(BaseModel):
    total_sessions: int
    total_kwh: float
    total_cost: float
    avg_session_cost: float
    co2_saved_kg: float
    fuel_saved_liters: float
    top_station_name: str | None
    top_station_visits: int


class ClientRequestCreate(BaseModel):
    subject: str = Field(min_length=3, max_length=120)
    message: str = Field(min_length=5, max_length=2000)


class ClientRequestUpdate(BaseModel):
    status: str | None = None
    admin_comment: str | None = Field(default=None, max_length=1000)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip().lower()
        if normalized not in ALLOWED_REQUEST_STATUSES:
            raise ValueError("Invalid request status")
        return normalized


class ClientRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    user_email: str | None = None
    user_full_name: str | None = None
    subject: str
    message: str
    status: str
    admin_comment: str | None
    created_at: datetime
    updated_at: datetime | None


class ClientRequestListResponse(BaseModel):
    items: list[ClientRequestOut]
    total: int
    page: int
    limit: int


class ChatMessageCreate(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    user_id: int | None = Field(default=None, gt=0)


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    sender_role: str
    message: str
    created_at: datetime


class AdminRentalTimelineItem(BaseModel):
    rental_id: int
    start_date: date
    end_date: date
    total_price: float
    status: str
    user_id: int
    user_email: str
    user_full_name: str | None
    car_id: int
    car_brand: str
    car_model: str
    car_category: str


class AdminRentalTimelineResponse(BaseModel):
    items: list[AdminRentalTimelineItem]
    total: int
    page: int
    limit: int


class AdminOverviewOut(BaseModel):
    total_users: int
    total_cars: int
    active_rentals: int
    completed_rentals: int
    monthly_revenue: float
    monthly_expenses: float
    monthly_profit: float
    avg_check: float
