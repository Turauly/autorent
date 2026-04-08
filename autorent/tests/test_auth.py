from app.core.security import hash_password
from app.models.user import User


def _login(client, email: str, password: str):
    return client.post(
        "/auth/login",
        data={"username": email, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )


def _auth_headers(client, email: str, password: str) -> dict[str, str]:
    response = _login(client, email, password)
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_login_success(client, db_session):
    user = User(
        email="user@example.com",
        password_hash=hash_password("secret123"),
        role="user",
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()

    response = _login(client, "user@example.com", "secret123")
    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert isinstance(payload["access_token"], str)
    assert payload["access_token"]


def test_login_rejects_wrong_password(client, db_session):
    user = User(
        email="user2@example.com",
        password_hash=hash_password("secret123"),
        role="user",
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()

    response = _login(client, "user2@example.com", "wrong-password")
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_user_cannot_access_admin_route(client, db_session):
    user = User(
        email="user3@example.com",
        password_hash=hash_password("secret123"),
        role="user",
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()

    headers = _auth_headers(client, "user3@example.com", "secret123")
    response = client.get("/admin/users", headers=headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Admin access required"


def test_admin_can_access_admin_route(client, db_session):
    admin = User(
        email="admin@example.com",
        password_hash=hash_password("admin123"),
        role="admin",
        is_verified=True,
    )
    db_session.add(admin)
    db_session.commit()

    headers = _auth_headers(client, "admin@example.com", "admin123")
    response = client.get("/admin/users", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
