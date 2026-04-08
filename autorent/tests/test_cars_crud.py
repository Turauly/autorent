from app.core.security import hash_password
from app.models.user import User


def _auth_headers(client, email: str, password: str) -> dict[str, str]:
    response = client.post(
        "/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _create_admin(client, db_session):
    admin = User(
        email="cars-admin@example.com",
        password_hash=hash_password("admin123"),
        role="admin",
        is_verified=True,
    )
    db_session.add(admin)
    db_session.commit()
    return _auth_headers(client, "cars-admin@example.com", "admin123")


def test_admin_can_create_update_delete_car(client, db_session):
    headers = _create_admin(client, db_session)

    create_response = client.post(
        "/cars/",
        json={
            "brand": "Toyota",
            "model": "Camry",
            "year": 2022,
            "price_per_day": 25000,
            "status": "available",
            "category": "comfort",
            "is_electric": True,
            "battery_capacity_kwh": 77.4,
            "range_km": 520,
            "charge_port": "CCS2",
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    created = create_response.json()
    car_id = created["id"]
    assert created["brand"] == "Toyota"
    assert created["is_electric"] is True
    assert created["charge_port"] == "CCS2"

    update_response = client.put(
        f"/cars/{car_id}",
        json={
            "price_per_day": 27000,
            "status": "service",
            "category": "lux",
        },
        headers=headers,
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["price_per_day"] == 27000
    assert updated["status"] == "service"
    assert updated["category"] == "lux"

    delete_response = client.delete(f"/cars/{car_id}", headers=headers)
    assert delete_response.status_code == 204

    get_deleted = client.get(f"/cars/{car_id}")
    assert get_deleted.status_code == 404


def test_car_listing_search_filter_sort_pagination(client, db_session):
    headers = _create_admin(client, db_session)
    cars = [
        {"brand": "Hyundai", "model": "Elantra", "year": 2021, "price_per_day": 18000, "status": "available", "category": "budget"},
        {"brand": "Hyundai", "model": "Sonata", "year": 2023, "price_per_day": 26000, "status": "available", "category": "comfort"},
        {"brand": "Toyota", "model": "Corolla", "year": 2020, "price_per_day": 17000, "status": "rented", "category": "econom"},
    ]
    for payload in cars:
        response = client.post("/cars/", json=payload, headers=headers)
        assert response.status_code == 201

    response = client.get("/cars/?q=Hyundai&status=available&sort_by=price_per_day&sort_order=asc&page=1&limit=1")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert payload["page"] == 1
    assert payload["limit"] == 1
    assert len(payload["items"]) == 1
    assert payload["items"][0]["brand"] == "Hyundai"


def test_can_filter_electric_cars(client, db_session):
    headers = _create_admin(client, db_session)
    cars = [
        {
            "brand": "Tesla",
            "model": "Model 3",
            "year": 2024,
            "price_per_day": 42000,
            "status": "available",
            "category": "lux",
            "is_electric": True,
            "battery_capacity_kwh": 75,
            "range_km": 560,
            "charge_port": "CCS2",
        },
        {
            "brand": "Toyota",
            "model": "Corolla",
            "year": 2022,
            "price_per_day": 17000,
            "status": "available",
            "category": "econom",
        },
    ]
    for payload in cars:
        response = client.post("/cars/", json=payload, headers=headers)
        assert response.status_code == 201

    response = client.get("/cars/?is_electric=true")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["items"][0]["brand"] == "Tesla"
