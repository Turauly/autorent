from datetime import date, timedelta

from app.core.security import hash_password
from app.models.car import Car
from app.models.user import User


def _auth_headers(client, email: str, password: str) -> dict[str, str]:
    response = client.post(
        "/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_user_can_create_and_list_own_rentals(client, db_session):
    user = User(
        email="rental-user@example.com",
        password_hash=hash_password("user123"),
        role="user",
        is_verified=True,
    )
    car = Car(
        brand="Kia",
        model="K5",
        year=2022,
        price_per_day=20000,
        status="available",
        category="comfort",
    )
    db_session.add(user)
    db_session.add(car)
    db_session.commit()

    headers = _auth_headers(client, "rental-user@example.com", "user123")
    start = date.today()
    end = start + timedelta(days=3)

    create_response = client.post(
        "/rentals/",
        json={
            "car_id": car.id,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["status"] == "active"
    assert created["total_price"] == 3 * 20000

    my_rentals = client.get("/rentals/my?page=1&limit=10", headers=headers)
    assert my_rentals.status_code == 200
    payload = my_rentals.json()
    assert payload["total"] == 1
    assert payload["items"][0]["id"] == created["id"]


def test_user_can_complete_own_rental(client, db_session):
    user = User(
        email="rental-user2@example.com",
        password_hash=hash_password("user123"),
        role="user",
        is_verified=True,
    )
    car = Car(
        brand="Hyundai",
        model="Sonata",
        year=2021,
        price_per_day=18000,
        status="available",
        category="comfort",
    )
    db_session.add(user)
    db_session.add(car)
    db_session.commit()

    headers = _auth_headers(client, "rental-user2@example.com", "user123")
    start = date.today()
    end = start + timedelta(days=2)
    create_response = client.post(
        "/rentals/",
        json={
            "car_id": car.id,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    rental_id = create_response.json()["id"]

    complete_response = client.patch(f"/rentals/{rental_id}/complete", headers=headers)
    assert complete_response.status_code == 200
    assert complete_response.json()["message"] == "Rental completed successfully"

    db_session.refresh(car)
    assert car.status == "available"


def test_user_can_create_charging_session_for_electric_rental(client, db_session):
    user = User(
        email="ev-user@example.com",
        password_hash=hash_password("user123"),
        role="user",
        is_verified=True,
    )
    car = Car(
        brand="BYD",
        model="Seal",
        year=2024,
        price_per_day=32000,
        status="available",
        category="comfort",
        is_electric=True,
        battery_capacity_kwh=82.5,
        range_km=570,
        charge_port="CCS2",
    )
    db_session.add_all([user, car])
    db_session.commit()
    db_session.refresh(car)

    headers = _auth_headers(client, "ev-user@example.com", "user123")
    station_response = client.post(
        "/charging-stations/",
        json={
            "name": "Mega Silk Way Hub",
            "city": "Astana",
            "address": "Kabanbay Batyr 62",
            "charger_type": "DC",
            "connector_types": "CCS2, Type 2",
            "slot_count": 4,
            "power_kw": 120,
            "price_per_kwh": 95,
            "is_available": True,
        },
        headers={
            **headers,
        },
    )
    assert station_response.status_code == 403

    admin = User(
        email="ev-admin@example.com",
        password_hash=hash_password("admin123"),
        role="admin",
        is_verified=True,
    )
    db_session.add(admin)
    db_session.commit()
    admin_headers = _auth_headers(client, "ev-admin@example.com", "admin123")
    station_response = client.post(
        "/charging-stations/",
        json={
            "name": "Mega Silk Way Hub",
            "city": "Astana",
            "address": "Kabanbay Batyr 62",
            "charger_type": "DC",
            "connector_types": "CCS2, Type 2",
            "slot_count": 4,
            "power_kw": 120,
            "price_per_kwh": 95,
            "is_available": True,
        },
        headers=admin_headers,
    )
    assert station_response.status_code == 201
    station_id = station_response.json()["id"]

    start = date.today()
    end = start + timedelta(days=2)
    create_response = client.post(
        "/rentals/",
        json={
            "car_id": car.id,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    rental_id = create_response.json()["id"]

    session_response = client.post(
        "/charging-stations/sessions",
        json={
            "rental_id": rental_id,
            "station_id": station_id,
            "charged_at": start.isoformat(),
            "kwh_amount": 38.5,
            "duration_minutes": 42,
            "battery_percent_start": 22,
            "battery_percent_end": 88,
        },
        headers=headers,
    )
    assert session_response.status_code == 201
    session = session_response.json()
    assert session["total_cost"] == 3657.5
    assert session["station_name"] == "Mega Silk Way Hub"

    list_response = client.get("/charging-stations/sessions/my", headers=headers)
    assert list_response.status_code == 200
    payload = list_response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["car_brand"] == "BYD"

    filtered_stations = client.get("/charging-stations/?connector_type=ccs2&available_only=true")
    assert filtered_stations.status_code == 200
    assert filtered_stations.json()["total"] == 1

    availability_response = client.patch(
        f"/charging-stations/{station_id}/availability",
        json={"is_available": False},
        headers=admin_headers,
    )
    assert availability_response.status_code == 200
    assert availability_response.json()["is_available"] is False


def test_charging_features_booking_reviews_analytics_notifications(client, db_session):
    user = User(
        email="ev-suite-user@example.com",
        password_hash=hash_password("user123"),
        role="user",
        is_verified=True,
    )
    admin = User(
        email="ev-suite-admin@example.com",
        password_hash=hash_password("admin123"),
        role="admin",
        is_verified=True,
    )
    car = Car(
        brand="Tesla",
        model="Model Y",
        year=2024,
        price_per_day=45000,
        status="available",
        category="lux",
        is_electric=True,
        battery_capacity_kwh=75,
        range_km=533,
        charge_port="CCS2",
    )
    db_session.add_all([user, admin, car])
    db_session.commit()
    db_session.refresh(car)

    user_headers = _auth_headers(client, "ev-suite-user@example.com", "user123")
    admin_headers = _auth_headers(client, "ev-suite-admin@example.com", "admin123")

    station_response = client.post(
        "/charging-stations/",
        json={
            "name": "Keruen Charge",
            "city": "Astana",
            "address": "Dostyk 9",
            "charger_type": "DC",
            "connector_types": "CCS2, Type 2",
            "slot_count": 5,
            "power_kw": 150,
            "price_per_kwh": 110,
            "latitude": 51.1282,
            "longitude": 71.4304,
            "is_available": True,
        },
        headers=admin_headers,
    )
    assert station_response.status_code == 201
    station = station_response.json()

    booking_response = client.post(
        "/charging-stations/bookings",
        json={
            "station_id": station["id"],
            "booking_date": date.today().isoformat(),
            "start_time": "10:00",
            "end_time": "11:00",
            "note": "Morning charge",
        },
        headers=user_headers,
    )
    assert booking_response.status_code == 201
    assert booking_response.json()["station_name"] == "Keruen Charge"

    my_bookings = client.get("/charging-stations/bookings/my", headers=user_headers)
    assert my_bookings.status_code == 200
    assert my_bookings.json()["total"] == 1

    all_bookings = client.get("/charging-stations/bookings", headers=admin_headers)
    assert all_bookings.status_code == 200
    booking_id = all_bookings.json()["items"][0]["id"]

    approve_booking = client.patch(
        f"/charging-stations/bookings/{booking_id}",
        json={"status": "completed"},
        headers=admin_headers,
    )
    assert approve_booking.status_code == 200
    assert approve_booking.json()["status"] == "completed"

    create_rental_response = client.post(
        "/rentals/",
        json={
            "car_id": car.id,
            "start_date": date.today().isoformat(),
            "end_date": (date.today() + timedelta(days=2)).isoformat(),
        },
        headers=user_headers,
    )
    assert create_rental_response.status_code == 201
    rental_id = create_rental_response.json()["id"]

    session_response = client.post(
        "/charging-stations/sessions",
        json={
            "rental_id": rental_id,
            "station_id": station["id"],
            "charged_at": date.today().isoformat(),
            "kwh_amount": 20,
            "battery_percent_start": 30,
            "battery_percent_end": 85,
        },
        headers=user_headers,
    )
    assert session_response.status_code == 201

    review_response = client.post(
        "/charging-stations/reviews",
        json={
            "station_id": station["id"],
            "rating": 5,
            "comment": "Very fast charger",
        },
        headers=user_headers,
    )
    assert review_response.status_code == 201
    assert review_response.json()["rating"] == 5

    list_reviews = client.get(f"/charging-stations/reviews?station_id={station['id']}")
    assert list_reviews.status_code == 200
    assert list_reviews.json()["total"] == 1

    filtered_stations = client.get("/charging-stations/?sort_by=power_kw&sort_order=desc&connector_type=type 2")
    assert filtered_stations.status_code == 200
    assert filtered_stations.json()["items"][0]["review_count"] == 1

    analytics_response = client.get("/charging-stations/analytics/my", headers=user_headers)
    assert analytics_response.status_code == 200
    analytics = analytics_response.json()
    assert analytics["total_sessions"] == 1
    assert analytics["total_kwh"] == 20
    assert analytics["co2_saved_kg"] > 0

    notifications_response = client.get("/charging-stations/notifications/my", headers=user_headers)
    assert notifications_response.status_code == 200
    notifications = notifications_response.json()
    assert notifications["total"] >= 4

    notification_id = notifications["items"][0]["id"]
    mark_response = client.patch(
        f"/charging-stations/notifications/{notification_id}",
        json={"is_read": True},
        headers=user_headers,
    )
    assert mark_response.status_code == 200
    assert mark_response.json()["is_read"] is True
