import pytest
from httpx import AsyncClient

async def get_token_for(client: AsyncClient, email: str, password: str) -> str:
    res = await client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200
    return res.json()["access_token"]

@pytest.mark.asyncio
async def test_student_can_view_own_grades_and_overview(client: AsyncClient):
    token = await get_token_for(client, "elev.andrei@edugrade.ro", "Elev123!")
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.get("/api/grades", headers=headers)
    assert res.status_code == 200
    grades = res.json()
    assert len(grades) > 0
    assert all(g["elev_nume"] == "Andrei Popescu" for g in grades)

    overview_res = await client.get("/api/grades/my-overview", headers=headers)
    assert overview_res.status_code == 200
    overview = overview_res.json()
    assert overview["elev_nume"] == "Andrei Popescu"
    assert overview["medie_generala"] is not None
    assert overview["medie_generala"] >= 9.0
    assert len(overview["materii"]) > 0

@pytest.mark.asyncio
async def test_parent_monitors_children_grades_remotely(client: AsyncClient):
    parent_token = await get_token_for(client, "parinte.popescu@edugrade.ro", "Parinte123!")
    headers = {"Authorization": f"Bearer {parent_token}"}

    children_res = await client.get("/api/parent/children", headers=headers)
    assert children_res.status_code == 200
    children = children_res.json()
    assert len(children) >= 2
    andrei = next(c for c in children if c["nume"] == "Andrei Popescu")

    overview_res = await client.get(f"/api/grades/student/{andrei['id_utilizator']}/overview", headers=headers)
    assert overview_res.status_code == 200
    data = overview_res.json()
    assert data["elev_nume"] == "Andrei Popescu"
    assert data["medie_generala"] is not None

@pytest.mark.asyncio
async def test_teacher_adds_grade_and_notifies_student_and_parent(client: AsyncClient):
    teacher_token = await get_token_for(client, "prof.ionescu@edugrade.ro", "Profesor123!")
    teacher_headers = {"Authorization": f"Bearer {teacher_token}"}

    andrei_token = await get_token_for(client, "elev.andrei@edugrade.ro", "Elev123!")
    andrei_profile = (await client.get("/api/auth/me", headers={"Authorization": f"Bearer {andrei_token}"})).json()
    andrei_id = andrei_profile["id_utilizator"]

    subjects = (await client.get("/api/subjects", headers=teacher_headers)).json()
    mate = next(s for s in subjects if s["cod"] == "MATE")

    grade_payload = {
        "elev_id": andrei_id,
        "materie_id": mate["id"],
        "valoare": 10,
        "tip_evaluare": "PROIECT",
        "observatii": "Proiect remarcabil despre numere prime",
    }
    create_res = await client.post("/api/grades", json=grade_payload, headers=teacher_headers)
    assert create_res.status_code == 201
    created_grade = create_res.json()
    assert created_grade["valoare"] == 10

    notifs_elev = (await client.get("/api/notifications", headers={"Authorization": f"Bearer {andrei_token}"})).json()
    assert any("Nota noua: 10 la Matematica" in n["titlu"] for n in notifs_elev)

    parent_token = await get_token_for(client, "parinte.popescu@edugrade.ro", "Parinte123!")
    notifs_parent = (await client.get("/api/notifications", headers={"Authorization": f"Bearer {parent_token}"})).json()
    assert any("Nota copil: Andrei Popescu a primit 10 la Matematica" in n["titlu"] for n in notifs_parent)

@pytest.mark.asyncio
async def test_absences_and_motivate(client: AsyncClient):
    teacher_token = await get_token_for(client, "prof.ionescu@edugrade.ro", "Profesor123!")
    andrei_token = await get_token_for(client, "elev.andrei@edugrade.ro", "Elev123!")
    andrei_id = (await client.get("/api/auth/me", headers={"Authorization": f"Bearer {andrei_token}"})).json()["id_utilizator"]

    abs_res = await client.get("/api/absences", headers={"Authorization": f"Bearer {andrei_token}"})
    assert abs_res.status_code == 200
    abs_data = abs_res.json()
    assert abs_data["total_absente"] >= 1
    assert "absente" in abs_data

    unmotivated = next((a for a in abs_data["absente"] if not a["este_motivata"]), None)
    if unmotivated:
        mot_res = await client.patch(
            f"/api/absences/{unmotivated['id']}/motivate",
            json={"este_motivata": True, "motiv": "Scutire medicala confirmata"},
            headers={"Authorization": f"Bearer {teacher_token}"},
        )
        assert mot_res.status_code == 200
        assert mot_res.json()["este_motivata"] is True

@pytest.mark.asyncio
async def test_remarks_and_mentions(client: AsyncClient):
    teacher_token = await get_token_for(client, "prof.ionescu@edugrade.ro", "Profesor123!")
    andrei_token = await get_token_for(client, "elev.andrei@edugrade.ro", "Elev123!")
    andrei_id = (await client.get("/api/auth/me", headers={"Authorization": f"Bearer {andrei_token}"})).json()["id_utilizator"]

    remark_res = await client.post(
        "/api/remarks",
        json={
            "elev_id": andrei_id,
            "tip": "MENTIUNE",
            "titlu": "Locul II - Concursul de Fizica Pas cu Pas",
            "descriere": "Rezultat excelent la rezolvarea problemelor experimentale.",
        },
        headers={"Authorization": f"Bearer {teacher_token}"},
    )
    assert remark_res.status_code == 201

    get_res = await client.get("/api/remarks", headers={"Authorization": f"Bearer {andrei_token}"})
    assert get_res.status_code == 200
    remarks = get_res.json()
    assert any("Concursul de Fizica" in r["titlu"] for r in remarks)

@pytest.mark.asyncio
async def test_dashboard_summary_for_student_and_parent(client: AsyncClient):
    andrei_token = await get_token_for(client, "elev.andrei@edugrade.ro", "Elev123!")
    dash_res = await client.get("/api/dashboard", headers={"Authorization": f"Bearer {andrei_token}"})
    assert dash_res.status_code == 200
    dash = dash_res.json()
    assert dash["rol"] == "ELEV"
    assert dash["nume"] == "Andrei Popescu"
    assert dash["total_note"] > 0
    assert dash["medie_generala"] is not None
    assert len(dash["recent_grades"]) > 0

@pytest.mark.asyncio
async def test_classes_and_subjects_endpoints(client: AsyncClient):
    token = await get_token_for(client, "admin@edugrade.ro", "Admin123!")
    headers = {"Authorization": f"Bearer {token}"}

    classes_res = await client.get("/api/classes", headers=headers)
    assert classes_res.status_code == 200
    assert len(classes_res.json()) >= 2

    subjects_res = await client.get("/api/subjects", headers=headers)
    assert subjects_res.status_code == 200
    assert len(subjects_res.json()) >= 6
