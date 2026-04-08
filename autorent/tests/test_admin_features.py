from datetime import date, timedelta

from app.core.security import hash_password
from app.models.car import Car
from app.models.rental import Rental
from app.models.user import User


def _auth_headers(client, email: str, password: str) -> dict[str, str]:
    response = client.post(
        "/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _seed_admin_and_user(db_session) -> tuple[User, User]:
    admin = User(
        email="week6-admin@example.com",
        password_hash=hash_password("admin123"),
        role="admin",
        is_verified=True,
    )
    user = User(
        email="week6-user@example.com",
        password_hash=hash_password("user123"),
        role="user",
        is_verified=True,
    )
    db_session.add_all([admin, user])
    db_session.commit()
    db_session.refresh(admin)
    db_session.refresh(user)
    return admin, user


def test_admin_overview_and_expense_audit_flow(client, db_session):
    _, user = _seed_admin_and_user(db_session)
    car = Car(
        brand="Toyota",
        model="Camry",
        year=2023,
        price_per_day=25000,
        status="available",
        category="comfort",
    )
    db_session.add(car)
    db_session.commit()
    db_session.refresh(car)

    today = date.today()
    rental = Rental(
        user_id=user.id,
        car_id=car.id,
        start_date=today,
        end_date=today + timedelta(days=2),
        total_price=50000,
        status="active",
    )
    db_session.add(rental)
    db_session.commit()

    admin_headers = _auth_headers(client, "week6-admin@example.com", "admin123")

    expense_response = client.post(
        "/admin/expenses",
        headers=admin_headers,
        json={
            "title": "Car wash",
            "amount": 5000,
            "category": "operations",
            "expense_date": today.isoformat(),
            "note": "Monthly cleaning",
        },
    )
    assert expense_response.status_code == 201
    created_expense = expense_response.json()
    assert created_expense["amount"] == 5000

    overview_response = client.get("/admin/overview", headers=admin_headers)
    assert overview_response.status_code == 200
    overview = overview_response.json()
    assert overview["total_users"] == 2
    assert overview["total_cars"] == 1
    assert overview["active_rentals"] == 1
    assert overview["monthly_revenue"] == 50000
    assert overview["monthly_expenses"] == 5000
    assert overview["monthly_profit"] == 45000

    logs_response = client.get("/admin/audit-logs?action=expense_created", headers=admin_headers)
    assert logs_response.status_code == 200
    logs_payload = logs_response.json()
    assert logs_payload["total"] >= 1
    assert any(item["action"] == "expense_created" for item in logs_payload["items"])


def test_client_request_flow_user_to_admin(client, db_session):
    _, user = _seed_admin_and_user(db_session)
    user_headers = _auth_headers(client, "week6-user@example.com", "user123")
    admin_headers = _auth_headers(client, "week6-admin@example.com", "admin123")

    create_response = client.post(
        "/profile/requests",
        headers=user_headers,
        json={"subject": "Order issue", "message": "Please help with my rental status"},
    )
    assert create_response.status_code == 201
    created = create_response.json()
    request_id = created["id"]
    assert created["status"] == "open"
    assert created["user_id"] == user.id

    my_requests_response = client.get("/profile/requests", headers=user_headers)
    assert my_requests_response.status_code == 200
    assert len(my_requests_response.json()) == 1

    admin_list_response = client.get("/admin/client-requests?status_filter=open", headers=admin_headers)
    assert admin_list_response.status_code == 200
    list_payload = admin_list_response.json()
    assert list_payload["total"] >= 1
    assert any(item["id"] == request_id for item in list_payload["items"])

    update_response = client.patch(
        f"/admin/client-requests/{request_id}",
        headers=admin_headers,
        json={"status": "resolved", "admin_comment": "Issue solved"},
    )
    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["status"] == "resolved"
    assert updated["admin_comment"] == "Issue solved"

    missing_response = client.patch(
        "/admin/client-requests/9999",
        headers=admin_headers,
        json={"status": "resolved"},
    )
    assert missing_response.status_code == 404


def test_admin_rental_timeline_filtering(client, db_session):
    _, user = _seed_admin_and_user(db_session)
    admin_headers = _auth_headers(client, "week6-admin@example.com", "admin123")

    car_1 = Car(
        brand="Hyundai",
        model="Elantra",
        year=2022,
        price_per_day=18000,
        status="available",
        category="budget",
    )
    car_2 = Car(
        brand="Kia",
        model="K5",
        year=2021,
        price_per_day=21000,
        status="available",
        category="comfort",
    )
    db_session.add_all([car_1, car_2])
    db_session.commit()
    db_session.refresh(car_1)
    db_session.refresh(car_2)

    today = date.today()
    rentals = [
        Rental(
            user_id=user.id,
            car_id=car_1.id,
            start_date=today,
            end_date=today + timedelta(days=1),
            total_price=18000,
            status="active",
        ),
        Rental(
            user_id=user.id,
            car_id=car_2.id,
            start_date=today,
            end_date=today + timedelta(days=2),
            total_price=42000,
            status="completed",
        ),
    ]
    db_session.add_all(rentals)
    db_session.commit()

    all_response = client.get("/admin/rental-timeline?page=1&limit=10", headers=admin_headers)
    assert all_response.status_code == 200
    all_payload = all_response.json()
    assert all_payload["total"] == 2
    assert len(all_payload["items"]) == 2

    filtered_response = client.get(
        f"/admin/rental-timeline?user_id={user.id}&status_filter=completed",
        headers=admin_headers,
    )
    assert filtered_response.status_code == 200
    filtered_payload = filtered_response.json()
    assert filtered_payload["total"] == 1
    assert filtered_payload["items"][0]["status"] == "completed"
