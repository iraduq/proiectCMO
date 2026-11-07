import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_seed_users_login(client: AsyncClient):
    response = await client.post(
        "/api/auth/login",
        json={"email": "elev.andrei@edugrade.ro", "password": "Elev123!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "ELEV"
    assert data["nume"] == "Andrei Popescu"

    response_p = await client.post(
        "/api/auth/login",
        json={"email": "parinte.popescu@edugrade.ro", "password": "Parinte123!"},
    )
    assert response_p.status_code == 200
    data_p = response_p.json()
    assert data_p["role"] == "PARINTE"

    response_prof = await client.post(
        "/api/auth/login",
        json={"email": "prof.ionescu@edugrade.ro", "password": "Profesor123!"},
    )
    assert response_prof.status_code == 200
    assert response_prof.json()["role"] == "PROFESOR"

@pytest.mark.asyncio
async def test_register_new_student(client: AsyncClient):
    payload = {
        "nume": "Mihai Stoica",
        "email": "mihai.stoica@edugrade.ro",
        "password": "Password123!",
        "rol": "ELEV",
        "numar_matricol": "MAT-10A-099",
    }
    response = await client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == payload["email"]
    assert data["role"] == "ELEV"
    assert "access_token" in data

@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    payload = {
        "nume": "Andrei Clona",
        "email": "elev.andrei@edugrade.ro",
        "password": "Password123!",
        "rol": "ELEV",
    }
    response = await client.post("/api/auth/register", json=payload)
    assert response.status_code == 409
    assert response.json()["code"] == "user_email_already_exists"

@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    payload = {
        "email": "elev.andrei@edugrade.ro",
        "password": "WrongPassword123!",
    }
    response = await client.post("/api/auth/login", json=payload)
    assert response.status_code == 401
    assert response.json()["code"] == "invalid_credentials"

@pytest.mark.asyncio
async def test_google_login_bonus(client: AsyncClient):
    payload = {
        "id_token": "google_test_token_student_999",
        "role": "ELEV",
    }
    response = await client.post("/api/auth/google", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "ELEV"

@pytest.mark.asyncio
async def test_get_current_user_profile(client: AsyncClient):
    login_res = await client.post(
        "/api/auth/login",
        json={"email": "parinte.popescu@edugrade.ro", "password": "Parinte123!"},
    )
    token = login_res.json()["access_token"]

    response = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "parinte.popescu@edugrade.ro"
    assert data["role"] == "PARINTE"
    assert len(data["copii"]) >= 1
    copil = data["copii"][0]
    assert copil["nume"] in ("Andrei Popescu", "Elena Popescu")
    assert copil["medie_generala"] is not None
