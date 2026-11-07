# 🎓 EduGrade - Backend Cloud pentru Catalog Digital Multi-Rol

Backend REST API securizat, scalabil si complet documentat pentru aplicatia Android **EduGrade**.

> **Descriere proiect**: EduGrade este un catalog digital multi-rol in care elevii isi pot vedea notele, mediile calculate si mentiunile/aprecierile, in timp ce parintii monitorizeaza de la distanta situatia scolara a copiilor, securizat in cloud. Cadrele didactice pot consemna note, absente si mentiuni, declansand notificari automate.

---

## 🎯 Conformitate cu Baremul de Notare (100p + 10p Bonus)

| Criteriu Barem | Punctaj Maxim | Implementare in EduGrade |
| :--- | :---: | :--- |
| **1. Autentificare & Validare** | **10 p** | JWT Token (`HS256`), bcrypt password hashing, validare Pydantic V2, suport multi-rol (`ELEV`, `PARINTE`, `PROFESOR`, `ADMINISTRATOR`). |
| **2. Stocare Cloud Date** | **20 p** | Baza de date relationala asincrona (SQLAlchemy 2.0 Async, aiosqlite / PostgreSQL), persistenta completa in cloud. |
| **3. Evenimente UI & Notificari** | **10 p** | Sistem dedicat de notificari push/in-app (`/api/notifications`), contor necitite (badge), alerte automate la note si absente noi. |
| **4. Activitati & Meniu Functional** | **20 p** | Endpoints grupate logic pentru minim 3 activitati Android (Auth, Dashboard/Situatie, Detalii Note/Absente/Mentiuni) si optiuni de meniu (Filtrare materii, Comutare copil parinte, Logout). |
| **5. Design & Experienta (UX)** | **20 p** | Mesaje de eroare explicite in limba romana (`AppException`), coduri HTTP standard (200, 201, 400, 401, 403, 404, 409, 422). |
| **6. Bune Practici & Modularitate** | **20 p** | Clean Architecture (Routers -> Services -> Repositories -> Models), type hinting strict, 14 teste automate trecute 100%. |
| **7. Bonus: Google Sign-In** | **5 p** | Endpoint dedicat `POST /api/auth/google` pentru integrarea autentificarii cu Google in Android. |
| **8. Bonus: Complexitate & Analytics** | **5 p** | `GET /api/dashboard` si calcul dinamic ponderat al mediilor pe materii si a mediei generale + rang clasa. |

---

## 👥 Conturi Pre-populate pentru Testare si Prezentare

La prima pornire a serverului, baza de date este populata automat cu scenariul complet:

| Rol | Email | Parola | Detalii & Scenariu |
| :--- | :--- | :--- | :--- |
| **Elev** | `elev.andrei@edugrade.ro` | `Elev123!` | Andrei Popescu, Clasa a X-a A (Mat-Info), matricol `MAT-10A-042`. Are note la Mate, Info, Romana, Fizica, medie generala 9.75, 1 mentiune olimpiada. |
| **Elev** | `elev.elena@edugrade.ro` | `Elev123!` | Elena Popescu, Clasa a X-a A, sora lui Andrei, matricol `MAT-10A-043`. |
| **Parinte** | `parinte.popescu@edugrade.ro` | `Parinte123!` | Maria Popescu - are asociati ambii copii (Andrei si Elena). Poate comuta intre ei si monitoriza notele, absentele si notificarile lor. |
| **Profesor** | `prof.ionescu@edugrade.ro` | `Profesor123!` | Prof. Radu Ionescu - Profesor de Matematica si Diriginte la Clasa a X-a A. |
| **Profesor** | `prof.popa@edugrade.ro` | `Profesor123!` | Prof. Mihaela Popa - Profesor de Informatica. |
| **Admin** | `admin@edugrade.ro` | `Admin123!` | Administrator Sistem - acces la managementul claselor, materiilor si asignarilor. |

---

## 🚀 Pornirea Rapida a Serverului

### 1. Activare mediu virtual & instalare dependinte
```bash
# Windows PowerShell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Pornire server uvicorn
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Documentatie Interactiva Swagger
Deschideti in browser:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Redoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 📱 Ghid de Conectare cu Android Studio

Consultati documentul detaliat [ANDROID_INTEGRATION_GUIDE.md](file:///d:/LabCMO/backend/ANDROID_INTEGRATION_GUIDE.md) pentru:
- Maparea activitatilor Android
- Configuratia Retrofit / OkHttp
- Adresa IP a emulatorului (`http://10.0.2.2:8000/api/`)
- Evenimentele UI recomandate (Click, Long Click, Swipe-to-Refresh)
- Meniul functional din Toolbar (OptionsMenu & NavigationDrawer)
