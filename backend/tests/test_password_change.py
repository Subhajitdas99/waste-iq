from app.core.security import verify_password
from app.models.user import User


def _register_and_get_headers(client, email, password="Test@1234", phone="9876543210"):
    response = client.post(
        "/auth/register",
        json={
            "name": "Password User",
            "email": email,
            "password": password,
            "phone": phone,
            "role": "citizen",
        },
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _change_password(client, headers, current_password, new_password):
    return client.post(
        "/auth/change-password",
        json={"current_password": current_password, "new_password": new_password},
        headers=headers,
    )


def test_change_password_requires_authentication(client):
    response = client.post(
        "/auth/change-password",
        json={"current_password": "Test@1234", "new_password": "NewPass@1234"},
    )
    assert response.status_code == 401


def test_change_password_success(client, db_session):
    headers = _register_and_get_headers(client, "change@example.com")
    response = _change_password(client, headers, "Test@1234", "NewPass@1234")
    assert response.status_code == 200
    body = response.json()
    assert body == {"message": "Password changed successfully"}
    assert "password_hash" not in body
    assert "current_password" not in body
    assert "new_password" not in body

    user = db_session.query(User).filter(User.email == "change@example.com").one()
    assert verify_password("NewPass@1234", user.password_hash)


def test_change_password_persists_new_hash(client, db_session):
    headers = _register_and_get_headers(client, "hashcheck@example.com")
    user = db_session.query(User).filter(User.email == "hashcheck@example.com").one()
    old_hash = user.password_hash

    response = _change_password(client, headers, "Test@1234", "Another@Pass1")
    assert response.status_code == 200

    db_session.refresh(user)
    assert user.password_hash != old_hash
    assert verify_password("Another@Pass1", user.password_hash)


def test_change_password_incorrect_current_password_fails(client, db_session):
    headers = _register_and_get_headers(client, "wrongcurrent@example.com")
    response = _change_password(client, headers, "WrongCurrent1", "NewPass@1234")
    assert response.status_code == 400

    user = db_session.query(User).filter(User.email == "wrongcurrent@example.com").one()
    assert verify_password("Test@1234", user.password_hash)


def test_change_password_same_password_fails(client, db_session):
    headers = _register_and_get_headers(client, "samepass@example.com")
    response = _change_password(client, headers, "Test@1234", "Test@1234")
    assert response.status_code == 400

    user = db_session.query(User).filter(User.email == "samepass@example.com").one()
    assert verify_password("Test@1234", user.password_hash)


def test_change_password_weak_new_password_fails(client, db_session):
    headers = _register_and_get_headers(client, "weakpass@example.com")
    response = _change_password(client, headers, "Test@1234", "short")
    assert response.status_code == 422

    user = db_session.query(User).filter(User.email == "weakpass@example.com").one()
    assert verify_password("Test@1234", user.password_hash)


def test_change_password_missing_fields_fails(client):
    headers = _register_and_get_headers(client, "missingfields@example.com")
    response = client.post("/auth/change-password", json={}, headers=headers)
    assert response.status_code == 422


def test_old_password_no_longer_authenticates_after_change(client):
    headers = _register_and_get_headers(client, "oldpass@example.com")
    response = _change_password(client, headers, "Test@1234", "NewPass@1234")
    assert response.status_code == 200

    old_login = client.post(
        "/auth/login", json={"email": "oldpass@example.com", "password": "Test@1234"}
    )
    assert old_login.status_code == 401


def test_new_password_authenticates_after_change(client):
    headers = _register_and_get_headers(client, "newpass@example.com")
    response = _change_password(client, headers, "Test@1234", "NewPass@1234")
    assert response.status_code == 200

    new_login = client.post(
        "/auth/login", json={"email": "newpass@example.com", "password": "NewPass@1234"}
    )
    assert new_login.status_code == 200
    assert "access_token" in new_login.json()


def test_current_token_still_valid_after_change(client):
    headers = _register_and_get_headers(client, "tokenstillvalid@example.com")
    response = _change_password(client, headers, "Test@1234", "NewPass@1234")
    assert response.status_code == 200

    me_response = client.get("/auth/me", headers=headers)
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "tokenstillvalid@example.com"
