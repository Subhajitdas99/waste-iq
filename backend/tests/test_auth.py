def test_register_citizen_success(client):
    response = client.post(
        "/auth/register",
        json={
            "name": "Fresh Citizen",
            "email": "fresh@example.com",
            "password": "Test@1234",
            "phone": "9876543210",
            "role": "citizen",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert "access_token" in body
    assert body["user"]["role"] == "citizen"
    assert body["user"]["email"] == "fresh@example.com"


def test_register_collector_success(client):
    response = client.post(
        "/auth/register",
        json={
            "name": "Fresh Collector",
            "email": "freshcollector@example.com",
            "password": "Test@1234",
            "phone": "9876543211",
            "role": "collector",
        },
    )
    assert response.status_code == 201
    assert response.json()["user"]["role"] == "collector"


def test_register_dealer_success(client):
    response = client.post(
        "/auth/register",
        json={
            "name": "Fresh Dealer",
            "email": "freshdealer@example.com",
            "password": "Test@1234",
            "phone": "9876543212",
            "role": "dealer",
        },
    )
    assert response.status_code == 201
    assert response.json()["user"]["role"] == "dealer"


def test_register_admin_without_code_fails(client):
    response = client.post(
        "/auth/register",
        json={
            "name": "Fake Admin",
            "email": "fakeadmin@example.com",
            "password": "Test@1234",
            "phone": "9876543213",
            "role": "admin",
        },
    )
    assert response.status_code == 400


def test_register_duplicate_email_fails(client):
    payload = {
        "name": "Dup User",
        "email": "dup@example.com",
        "password": "Test@1234",
        "phone": "9876543214",
        "role": "citizen",
    }
    first = client.post("/auth/register", json=payload)
    assert first.status_code == 201

    second_payload = {**payload, "phone": "9876543299"}
    second = client.post("/auth/register", json=second_payload)
    assert second.status_code == 400


def test_register_invalid_role_fails(client):
    response = client.post(
        "/auth/register",
        json={
            "name": "Bad Role",
            "email": "badrole@example.com",
            "password": "Test@1234",
            "phone": "9876543215",
            "role": "superuser",
        },
    )
    assert response.status_code == 422


def test_login_success(client):
    client.post(
        "/auth/register",
        json={
            "name": "Login User",
            "email": "login@example.com",
            "password": "Test@1234",
            "phone": "9876543216",
            "role": "citizen",
        },
    )
    response = client.post(
        "/auth/login", json={"email": "login@example.com", "password": "Test@1234"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_wrong_password_fails(client):
    client.post(
        "/auth/register",
        json={
            "name": "Login User 2",
            "email": "login2@example.com",
            "password": "Test@1234",
            "phone": "9876543217",
            "role": "citizen",
        },
    )
    response = client.post(
        "/auth/login", json={"email": "login2@example.com", "password": "WrongPassword"}
    )
    assert response.status_code == 401


def test_login_nonexistent_email_fails(client):
    response = client.post(
        "/auth/login", json={"email": "nobody@example.com", "password": "Test@1234"}
    )
    assert response.status_code == 401


def test_auth_me_with_valid_token(client, citizen_headers, citizen_user):
    response = client.get("/auth/me", headers=citizen_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == citizen_user.id
    assert body["email"] == citizen_user.email


def test_auth_me_without_token_fails(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


def test_auth_me_with_garbage_token_fails(client):
    response = client.get("/auth/me", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401
