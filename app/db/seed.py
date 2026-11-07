from datetime import datetime, timezone, timedelta
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import (
    Absence,
    EvaluationType,
    Grade,
    Notification,
    NotificationType,
    ParentStudent,
    Permission,
    Remark,
    RemarkType,
    Role,
    role_permissions,
    SchoolClass,
    Subject,
    TeacherClassSubject,
    User,
    UserRole,
)
from app.utils.roles import PERMISSION_DESCRIPTIONS, ROLE_PERMISSIONS_MAP, PermissionCode
from app.utils.security import get_password_hash

async def seed_roles_and_permissions(db: AsyncSession) -> dict[str, Role]:
    existing_perms = (await db.execute(select(Permission))).scalars().all()
    perms_by_code: dict[str, Permission] = {p.code: p for p in existing_perms}

    for perm_code in PermissionCode:
        if perm_code.value not in perms_by_code:
            desc = PERMISSION_DESCRIPTIONS.get(perm_code, perm_code.value)
            p = Permission(code=perm_code.value, description=desc)
            db.add(p)
            perms_by_code[perm_code.value] = p

    await db.flush()

    existing_roles = (await db.execute(select(Role))).scalars().all()
    roles_by_name: dict[str, Role] = {r.name: r for r in existing_roles}

    for role_enum in UserRole:
        role_name = role_enum.value
        if role_name not in roles_by_name:
            r = Role(name=role_name, description=f"Rol {role_name}")
            db.add(r)
            roles_by_name[role_name] = r

    await db.flush()

    existing_links = (await db.execute(select(role_permissions))).all()
    existing_set = {(r[0], r[1]) for r in existing_links}

    for role_enum in UserRole:
        role_obj = roles_by_name[role_enum.value]
        allowed_codes = [c.value for c in ROLE_PERMISSIONS_MAP.get(role_enum, [])]
        for c in allowed_codes:
            if c in perms_by_code:
                perm_obj = perms_by_code[c]
                if (role_obj.id, perm_obj.id) not in existing_set:
                    await db.execute(
                        role_permissions.insert().values(role_id=role_obj.id, permission_id=perm_obj.id)
                    )
                    existing_set.add((role_obj.id, perm_obj.id))

    await db.flush()
    return roles_by_name

async def seed_all(db: AsyncSession) -> None:
    if db.bind and db.bind.dialect.name == "sqlite":
        try:
            await db.execute(text("ALTER TABLE utilizatori ADD COLUMN materie_id INTEGER REFERENCES materii(id)"))
            await db.commit()
        except Exception:
            await db.rollback()

        try:
            await db.execute(text("UPDATE utilizatori SET materie_id = (SELECT id FROM materii WHERE cod = 'MATE') WHERE email = 'prof.ionescu@edugrade.ro' AND materie_id IS NULL"))
            await db.execute(text("UPDATE utilizatori SET materie_id = (SELECT id FROM materii WHERE cod = 'INFO') WHERE email = 'prof.popa@edugrade.ro' AND materie_id IS NULL"))
            await db.commit()
        except Exception:
            await db.rollback()

    existing_admin = (await db.execute(select(User).where(User.email == "admin@edugrade.ro"))).scalars().first()
    if existing_admin:
        return

    roles = await seed_roles_and_permissions(db)

    admin = User(
        nume="Administrator Sistem",
        email="admin@edugrade.ro",
        parola_hash=get_password_hash("Admin123!"),
        role_id=roles[UserRole.ADMINISTRATOR.value].id,
        telefon="0711000000",
        is_active=True,
    )
    db.add(admin)

    prof_ionescu = User(
        nume="Prof. Radu Ionescu",
        email="prof.ionescu@edugrade.ro",
        parola_hash=get_password_hash("Profesor123!"),
        role_id=roles[UserRole.PROFESOR.value].id,
        telefon="0722111222",
        is_active=True,
    )
    prof_popa = User(
        nume="Prof. Mihaela Popa",
        email="prof.popa@edugrade.ro",
        parola_hash=get_password_hash("Profesor123!"),
        role_id=roles[UserRole.PROFESOR.value].id,
        telefon="0722333444",
        is_active=True,
    )
    db.add_all([prof_ionescu, prof_popa])
    await db.flush()

    clasa_10a = SchoolClass(
        nume="Clasa a X-a A",
        specializare="Matematica-Informatica bilingv",
        an_scolar="2024-2025",
        diriginte_id=prof_ionescu.id_utilizator,
        is_active=True,
    )
    clasa_11b = SchoolClass(
        nume="Clasa a XI-a B",
        specializare="Stiinte ale Naturii",
        an_scolar="2024-2025",
        diriginte_id=prof_popa.id_utilizator,
        is_active=True,
    )
    db.add_all([clasa_10a, clasa_11b])
    await db.flush()

    materii = [
        Subject(nume="Matematica", cod="MATE", descriere="Algebra si analiza matematica", coeficient_credite=4),
        Subject(nume="Informatica", cod="INFO", descriere="Programare structurata si algoritmi", coeficient_credite=4),
        Subject(nume="Limba si Literatura Romana", cod="ROM", descriere="Literatura clasica si gramatica", coeficient_credite=3),
        Subject(nume="Fizica", cod="FIZ", descriere="Mecanica si termodinamica", coeficient_credite=3),
        Subject(nume="Limba Engleza", cod="ENG", descriere="Limba engleza avansat C1", coeficient_credite=2),
        Subject(nume="Istorie", cod="IST", descriere="Istoria moderna si contemporana", coeficient_credite=2),
    ]
    db.add_all(materii)
    await db.flush()

    prof_ionescu.materie_id = materii[0].id
    prof_popa.materie_id = materii[1].id
    await db.flush()

    asocieri = [
        TeacherClassSubject(profesor_id=prof_ionescu.id_utilizator, clasa_id=clasa_10a.id, materie_id=materii[0].id),
        TeacherClassSubject(profesor_id=prof_popa.id_utilizator, clasa_id=clasa_10a.id, materie_id=materii[1].id),
    ]
    db.add_all(asocieri)
    await db.flush()

    elev_andrei = User(
        nume="Andrei Popescu",
        email="elev.andrei@edugrade.ro",
        parola_hash=get_password_hash("Elev123!"),
        role_id=roles[UserRole.ELEV.value].id,
        numar_matricol="MAT-10A-042",
        clasa_id=clasa_10a.id,
        telefon="0733111222",
        is_active=True,
    )
    elev_elena = User(
        nume="Elena Popescu",
        email="elev.elena@edugrade.ro",
        parola_hash=get_password_hash("Elev123!"),
        role_id=roles[UserRole.ELEV.value].id,
        numar_matricol="MAT-10A-043",
        clasa_id=clasa_10a.id,
        telefon="0733222333",
        is_active=True,
    )
    db.add_all([elev_andrei, elev_elena])
    await db.flush()

    parinte = User(
        nume="Maria Popescu",
        email="parinte.popescu@edugrade.ro",
        parola_hash=get_password_hash("Parinte123!"),
        role_id=roles[UserRole.PARINTE.value].id,
        telefon="0744999888",
        is_active=True,
    )
    db.add(parinte)
    await db.flush()

    legatura1 = ParentStudent(parinte_id=parinte.id_utilizator, elev_id=elev_andrei.id_utilizator, relatie="Mama")
    legatura2 = ParentStudent(parinte_id=parinte.id_utilizator, elev_id=elev_elena.id_utilizator, relatie="Mama")
    db.add_all([legatura1, legatura2])
    await db.flush()

    now = datetime.now(timezone.utc)
    note_andrei = [
        Grade(elev_id=elev_andrei.id_utilizator, profesor_id=prof_ionescu.id_utilizator, materie_id=materii[0].id, valoare=10, tip_evaluare="TEST", data_notare=now - timedelta(days=20), observatii="Test initial analiza"),
        Grade(elev_id=elev_andrei.id_utilizator, profesor_id=prof_ionescu.id_utilizator, materie_id=materii[0].id, valoare=9, tip_evaluare="ORAL", data_notare=now - timedelta(days=10), observatii="Raspuns oral matrice"),
        Grade(elev_id=elev_andrei.id_utilizator, profesor_id=prof_ionescu.id_utilizator, materie_id=materii[0].id, valoare=10, tip_evaluare="TEZA", data_notare=now - timedelta(days=2), observatii="Teza semestriala"),
        Grade(elev_id=elev_andrei.id_utilizator, profesor_id=prof_popa.id_utilizator, materie_id=materii[1].id, valoare=10, tip_evaluare="PROIECT", data_notare=now - timedelta(days=15), observatii="Implementare arbore binar"),
        Grade(elev_id=elev_andrei.id_utilizator, profesor_id=prof_popa.id_utilizator, materie_id=materii[1].id, valoare=10, tip_evaluare="TEST", data_notare=now - timedelta(days=5), observatii="Test algoritmi grafuri"),
        Grade(elev_id=elev_andrei.id_utilizator, profesor_id=prof_ionescu.id_utilizator, materie_id=materii[2].id, valoare=9, tip_evaluare="TEST", data_notare=now - timedelta(days=12), observatii="Eseu literatura clasica"),
        Grade(elev_id=elev_andrei.id_utilizator, profesor_id=prof_ionescu.id_utilizator, materie_id=materii[3].id, valoare=10, tip_evaluare="ACTIVITATE", data_notare=now - timedelta(days=7), observatii="Lucrare practica laborator"),
    ]
    note_elena = [
        Grade(elev_id=elev_elena.id_utilizator, profesor_id=prof_ionescu.id_utilizator, materie_id=materii[0].id, valoare=9, tip_evaluare="TEST", data_notare=now - timedelta(days=18), observatii="Calcul diferential"),
        Grade(elev_id=elev_elena.id_utilizator, profesor_id=prof_popa.id_utilizator, materie_id=materii[1].id, valoare=10, tip_evaluare="PROIECT", data_notare=now - timedelta(days=8), observatii="Proiect interfata web"),
        Grade(elev_id=elev_elena.id_utilizator, profesor_id=prof_ionescu.id_utilizator, materie_id=materii[2].id, valoare=10, tip_evaluare="TEZA", data_notare=now - timedelta(days=3), observatii="Teza limba romana"),
    ]
    db.add_all(note_andrei + note_elena)
    await db.flush()

    absente = [
        Absence(elev_id=elev_andrei.id_utilizator, profesor_id=prof_ionescu.id_utilizator, materie_id=materii[0].id, data=now - timedelta(days=14), este_motivata=True, data_motivare=now - timedelta(days=10), motiv="Scutire medicala vizata"),
        Absence(elev_id=elev_andrei.id_utilizator, profesor_id=prof_popa.id_utilizator, materie_id=materii[3].id, data=now - timedelta(days=1), este_motivata=False, motiv=None),
        Absence(elev_id=elev_elena.id_utilizator, profesor_id=prof_ionescu.id_utilizator, materie_id=materii[2].id, data=now - timedelta(days=22), este_motivata=True, data_motivare=now - timedelta(days=20), motiv="Cerere invoire familie"),
    ]
    db.add_all(absente)
    await db.flush()

    mentiuni = [
        Remark(
            elev_id=elev_andrei.id_utilizator,
            profesor_id=prof_popa.id_utilizator,
            tip="MENTIUNE",
            titlu="Premiul I la Olimpiada Judeteana de Informatica",
            descriere="Felicitari pentru punctajul maxim obtinut si calificarea la etapa nationala!",
            data=now - timedelta(days=11),
        ),
        Remark(
            elev_id=elev_andrei.id_utilizator,
            profesor_id=prof_ionescu.id_utilizator,
            tip="LAUDA",
            titlu="Excelenta la Matematica",
            descriere="Implicare remarcabila in rezolvarea problemelor de nivel avansat la tabla.",
            data=now - timedelta(days=4),
        ),
        Remark(
            elev_id=elev_elena.id_utilizator,
            profesor_id=prof_ionescu.id_utilizator,
            tip="LAUDA",
            titlu="Redactare deosebita la Romana",
            descriere="Eseu premiat in cadrul revistei liceului pentru creativitate si rigoare.",
            data=now - timedelta(days=6),
        ),
    ]
    db.add_all(mentiuni)
    await db.flush()

    notificari = [
        Notification(
            utilizator_id=elev_andrei.id_utilizator,
            titlu="Nota noua: 10 la Matematica",
            mesaj="Prof. Radu Ionescu a trecut nota 10 la Teza.",
            tip=NotificationType.NOTA.value,
            este_citita=False,
        ),
        Notification(
            utilizator_id=elev_andrei.id_utilizator,
            titlu="Mentiune noua acordata",
            mesaj="Ai primit Mentiunea 'Premiul I la Olimpiada Judeteana de Informatica'.",
            tip=NotificationType.MENTIUNE.value,
            este_citita=False,
        ),
        Notification(
            utilizator_id=parinte.id_utilizator,
            titlu="Nota copil: Andrei Popescu - 10 la Matematica",
            mesaj="Elevul Andrei Popescu a obtinut nota 10 la Teza de Matematica.",
            tip=NotificationType.NOTA.value,
            este_citita=False,
        ),
        Notification(
            utilizator_id=parinte.id_utilizator,
            titlu="Absenta copil: Andrei Popescu",
            mesaj="A fost consemnata o absenta la Fizica pe data de ieri.",
            tip=NotificationType.ABSENTA.value,
            este_citita=False,
        ),
    ]
    db.add_all(notificari)
    await db.commit()

async def seed_base(db: AsyncSession) -> None:
    await seed_all(db)
