from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.db.models import EvaluationType, NotificationType, RemarkType, UserRole

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    role: str
    nume: str
    email: str
    materie_id: Optional[int] = None
    materie_nume: Optional[str] = None

class LoginRequest(BaseModel):
    email: str = Field(..., json_schema_extra={"example": "elev.andrei@edugrade.ro"})
    password: str = Field(..., min_length=6, json_schema_extra={"example": "Elev123!"})

class GoogleAuthRequest(BaseModel):
    id_token: str = Field(..., description="Google OAuth2 ID Token din Android Google Sign-In SDK")
    role: Optional[UserRole] = Field(default=UserRole.ELEV, description="Rolul dorit daca este cont nou")

class RegisterRequest(BaseModel):
    nume: str = Field(..., min_length=3, max_length=100, json_schema_extra={"example": "Andrei Popescu"})
    email: str = Field(..., json_schema_extra={"example": "andrei.popescu@edugrade.ro"})
    password: str = Field(..., min_length=8, json_schema_extra={"example": "Parola123!"})
    rol: UserRole = Field(default=UserRole.ELEV)
    numar_matricol: Optional[str] = Field(default=None, json_schema_extra={"example": "MAT-10A-042"})
    telefon: Optional[str] = Field(default=None, json_schema_extra={"example": "0722123456"})
    clasa_id: Optional[int] = Field(default=None, description="ID-ul clasei pentru elevi")
    materie_id: Optional[int] = Field(default=None, description="ID-ul materiei pentru profesori")

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_utilizator: int
    nume: str
    email: str
    materie_id: Optional[int] = None
    materie_nume: Optional[str] = None
    role: str
    numar_matricol: Optional[str] = None
    telefon: Optional[str] = None
    avatar_url: Optional[str] = None
    clasa_id: Optional[int] = None
    clasa_nume: Optional[str] = None
    is_active: bool
    created_at: datetime

class ChildSummary(BaseModel):
    id_utilizator: int
    nume: str
    email: str
    numar_matricol: Optional[str] = None
    clasa_id: Optional[int] = None
    clasa_nume: Optional[str] = None
    relatie: str
    medie_generala: Optional[float] = None
    total_absente: int = 0
    total_absente_nemotivate: int = 0
    total_mentiuni: int = 0

class UserProfileResponse(UserResponse):
    copii: list[ChildSummary] = Field(default_factory=list)

class SchoolClassCreate(BaseModel):
    nume: str = Field(..., min_length=2, max_length=50, json_schema_extra={"example": "Clasa a X-a A"})
    specializare: Optional[str] = Field(default="Matematica-Informatica", json_schema_extra={"example": "Matematica-Informatica"})
    an_scolar: str = Field(default="2024-2025", json_schema_extra={"example": "2024-2025"})
    diriginte_id: Optional[int] = None

class SchoolClassResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nume: str
    specializare: Optional[str] = None
    an_scolar: str
    diriginte_id: Optional[int] = None
    diriginte_nume: Optional[str] = None
    numar_elevi: int = 0

class SubjectCreate(BaseModel):
    nume: str = Field(..., min_length=2, max_length=100, json_schema_extra={"example": "Matematica"})
    cod: str = Field(..., min_length=2, max_length=20, json_schema_extra={"example": "MATE"})
    descriere: Optional[str] = None
    coeficient_credite: int = Field(default=1, ge=1, le=10)

class SubjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nume: str
    cod: str
    descriere: Optional[str] = None
    coeficient_credite: int
    is_active: bool

class TeacherAssignmentCreate(BaseModel):
    profesor_id: int
    clasa_id: int
    materie_id: int

class TeacherAssignmentResponse(BaseModel):
    id: int
    profesor_id: int
    profesor_nume: str
    clasa_id: int
    clasa_nume: str
    materie_id: int
    materie_nume: str

class GradeCreate(BaseModel):
    elev_id: int
    materie_id: int
    valoare: int = Field(..., ge=1, le=10, json_schema_extra={"example": 10})
    tip_evaluare: str = Field(default="TEST", json_schema_extra={"example": "TEST"})
    data_notare: Optional[datetime] = None
    observatii: Optional[str] = Field(default=None, json_schema_extra={"example": "Test grila algoritmi"})

class GradeUpdate(BaseModel):
    valoare: Optional[int] = Field(default=None, ge=1, le=10)
    tip_evaluare: Optional[str] = None
    observatii: Optional[str] = None

class GradeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    elev_id: int
    elev_nume: str
    profesor_id: int
    profesor_nume: str
    materie_id: int
    materie_nume: str
    valoare: int
    tip_evaluare: str
    data_notare: datetime
    observatii: Optional[str] = None
    created_at: datetime

class SubjectGradesGroup(BaseModel):
    materie_id: int
    materie_nume: str
    materie_cod: str
    note: list[GradeResponse] = Field(default_factory=list)
    medie: Optional[float] = None

class StudentAcademicOverview(BaseModel):
    elev_id: int
    elev_nume: str
    numar_matricol: Optional[str] = None
    clasa_nume: Optional[str] = None
    materii: list[SubjectGradesGroup] = Field(default_factory=list)
    medie_generala: Optional[float] = None
    total_absente: int = 0
    total_absente_nemotivate: int = 0
    total_mentiuni: int = 0

class AbsenceCreate(BaseModel):
    elev_id: int
    materie_id: int
    data: Optional[datetime] = None
    este_motivata: bool = False
    motiv: Optional[str] = None

class AbsenceMotivateRequest(BaseModel):
    este_motivata: bool = True
    motiv: Optional[str] = Field(default="Motivata medical / scutire", json_schema_extra={"example": "Scutire medicala vizata"})

class AbsenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    elev_id: int
    elev_nume: str
    profesor_id: int
    profesor_nume: str
    materie_id: int
    materie_nume: str
    data: datetime
    este_motivata: bool
    data_motivare: Optional[datetime] = None
    motiv: Optional[str] = None
    created_at: datetime

class AbsenceSummary(BaseModel):
    total_absente: int
    total_motivate: int
    total_nemotivate: int
    absente: list[AbsenceResponse] = Field(default_factory=list)

class RemarkCreate(BaseModel):
    elev_id: int
    tip: str = Field(default="MENTIUNE", json_schema_extra={"example": "MENTIUNE"})
    titlu: str = Field(..., min_length=3, max_length=200, json_schema_extra={"example": "Locul I la Olimpiada de Matematica"})
    descriere: str = Field(..., min_length=5, max_length=1000, json_schema_extra={"example": "Felicitari pentru rezultatul excelent la faza judeteana!"})
    data: Optional[datetime] = None

class RemarkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    elev_id: int
    elev_nume: str
    profesor_id: int
    profesor_nume: str
    tip: str
    titlu: str
    descriere: str
    data: datetime
    created_at: datetime

class LinkChildRequest(BaseModel):
    numar_matricol: str = Field(..., json_schema_extra={"example": "MAT-10A-042"})
    relatie: str = Field(default="Parinte", json_schema_extra={"example": "Mama"})

class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    utilizator_id: int
    titlu: str
    mesaj: str
    tip: str
    este_citita: bool
    referinta_id: Optional[int] = None
    created_at: datetime

class UnreadCountResponse(BaseModel):
    unread_count: int

class DashboardSummary(BaseModel):
    rol: str
    nume: str
    total_note: int
    medie_generala: Optional[float] = None
    total_absente: int
    absente_nemotivate: int
    total_mentiuni: int
    recent_grades: list[GradeResponse] = Field(default_factory=list)
    recent_absences: list[AbsenceResponse] = Field(default_factory=list)
    recent_remarks: list[RemarkResponse] = Field(default_factory=list)
    unread_notifications: int
