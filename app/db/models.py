import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship
from app.db.database import Base

class UserRole(str, enum.Enum):
    ADMINISTRATOR = "ADMINISTRATOR"
    PROFESOR = "PROFESOR"
    ELEV = "ELEV"
    PARINTE = "PARINTE"

class EvaluationType(str, enum.Enum):
    ORAL = "ORAL"
    TEST = "TEST"
    TEZA = "TEZA"
    PROIECT = "PROIECT"
    ACTIVITATE = "ACTIVITATE"

class RemarkType(str, enum.Enum):
    MENTIUNE = "MENTIUNE"
    LAUDA = "LAUDA"
    OBSERVATIE = "OBSERVATIE"
    AVERTISMENT = "AVERTISMENT"

class NotificationType(str, enum.Enum):
    NOTA = "NOTA"
    ABSENTA = "ABSENTA"
    MENTIUNE = "MENTIUNE"
    SISTEM = "SISTEM"

class TimestampMixin:
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", Integer, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)

    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles", lazy="selectin")
    users = relationship("User", back_populates="role_rel")

class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)

    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

class ParentStudent(Base):
    __tablename__ = "parinti_elevi"
    __table_args__ = (
        UniqueConstraint("parinte_id", "elev_id", name="uq_parinte_elev"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    parinte_id = Column(Integer, ForeignKey("utilizatori.id_utilizator", ondelete="CASCADE"), nullable=False, index=True)
    elev_id = Column(Integer, ForeignKey("utilizatori.id_utilizator", ondelete="CASCADE"), nullable=False, index=True)
    relatie = Column(String(50), default="Parinte", nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)

    parinte = relationship("User", foreign_keys=[parinte_id], back_populates="legaturi_copii")
    elev = relationship("User", foreign_keys=[elev_id], back_populates="legaturi_parinti")

class SchoolClass(TimestampMixin, Base):
    __tablename__ = "clase"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nume = Column(String(100), unique=True, nullable=False, index=True)
    specializare = Column(String(150), nullable=True)
    an_scolar = Column(String(50), default="2024-2025", nullable=False)
    diriginte_id = Column(
        Integer,
        ForeignKey("utilizatori.id_utilizator", ondelete="SET NULL", use_alter=True, name="fk_clase_diriginte"),
        nullable=True,
    )
    is_active = Column(Boolean, default=True, nullable=False)

    diriginte = relationship("User", foreign_keys=[diriginte_id], back_populates="clasa_diriginte")
    elevi = relationship("User", foreign_keys="[User.clasa_id]", back_populates="clasa")
    predari = relationship("TeacherClassSubject", back_populates="clasa", cascade="all, delete-orphan")

class Subject(TimestampMixin, Base):
    __tablename__ = "materii"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nume = Column(String(100), unique=True, nullable=False, index=True)
    cod = Column(String(20), unique=True, nullable=False, index=True)
    descriere = Column(String(500), nullable=True)
    coeficient_credite = Column(Integer, default=1, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    predari = relationship("TeacherClassSubject", back_populates="materie", cascade="all, delete-orphan")
    note = relationship("Grade", back_populates="materie", cascade="all, delete-orphan")
    absente = relationship("Absence", back_populates="materie", cascade="all, delete-orphan")

class TeacherClassSubject(Base):
    __tablename__ = "profesori_materii_clase"
    __table_args__ = (
        UniqueConstraint("profesor_id", "clasa_id", "materie_id", name="uq_profesor_clasa_materie"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    profesor_id = Column(Integer, ForeignKey("utilizatori.id_utilizator", ondelete="CASCADE"), nullable=False, index=True)
    clasa_id = Column(Integer, ForeignKey("clase.id", ondelete="CASCADE"), nullable=False, index=True)
    materie_id = Column(Integer, ForeignKey("materii.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)

    profesor = relationship("User", foreign_keys=[profesor_id])
    clasa = relationship("SchoolClass", back_populates="predari")
    materie = relationship("Subject", back_populates="predari")

class User(Base):
    __tablename__ = "utilizatori"

    id_utilizator = Column(Integer, primary_key=True, index=True, autoincrement=True)
    nume = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    parola_hash = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    numar_matricol = Column(String(100), unique=True, nullable=True, index=True)
    telefon = Column(String(30), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    clasa_id = Column(Integer, ForeignKey("clase.id", ondelete="SET NULL"), nullable=True, index=True)
    materie_id = Column(Integer, ForeignKey("materii.id", ondelete="SET NULL"), nullable=True, index=True)
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

    role_rel = relationship("Role", back_populates="users", lazy="joined")
    clasa = relationship("SchoolClass", foreign_keys=[clasa_id], back_populates="elevi", lazy="joined")
    materie = relationship("Subject", foreign_keys=[materie_id], lazy="joined")
    clasa_diriginte = relationship("SchoolClass", foreign_keys="[SchoolClass.diriginte_id]", back_populates="diriginte", uselist=False)

    legaturi_copii = relationship("ParentStudent", foreign_keys="[ParentStudent.parinte_id]", back_populates="parinte", cascade="all, delete-orphan")
    legaturi_parinti = relationship("ParentStudent", foreign_keys="[ParentStudent.elev_id]", back_populates="elev", cascade="all, delete-orphan")

    note_primite = relationship("Grade", foreign_keys="[Grade.elev_id]", back_populates="elev", cascade="all, delete-orphan")
    absente_primite = relationship("Absence", foreign_keys="[Absence.elev_id]", back_populates="elev", cascade="all, delete-orphan")
    mentiuni_primite = relationship("Remark", foreign_keys="[Remark.elev_id]", back_populates="elev", cascade="all, delete-orphan")
    notificari = relationship("Notification", foreign_keys="[Notification.utilizator_id]", back_populates="utilizator", cascade="all, delete-orphan")

class Grade(TimestampMixin, Base):
    __tablename__ = "note"
    __table_args__ = (
        CheckConstraint("valoare >= 1 AND valoare <= 10", name="ck_valoare_nota_1_10"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    elev_id = Column(Integer, ForeignKey("utilizatori.id_utilizator", ondelete="CASCADE"), nullable=False, index=True)
    profesor_id = Column(Integer, ForeignKey("utilizatori.id_utilizator", ondelete="RESTRICT"), nullable=False, index=True)
    materie_id = Column(Integer, ForeignKey("materii.id", ondelete="RESTRICT"), nullable=False, index=True)
    valoare = Column(Integer, nullable=False)
    tip_evaluare = Column(String(50), default="ORAL", nullable=False)
    data_notare = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    observatii = Column(String(500), nullable=True)

    elev = relationship("User", foreign_keys=[elev_id], back_populates="note_primite", lazy="joined")
    profesor = relationship("User", foreign_keys=[profesor_id], lazy="joined")
    materie = relationship("Subject", back_populates="note", lazy="joined")

class Absence(TimestampMixin, Base):
    __tablename__ = "absente"

    id = Column(Integer, primary_key=True, autoincrement=True)
    elev_id = Column(Integer, ForeignKey("utilizatori.id_utilizator", ondelete="CASCADE"), nullable=False, index=True)
    profesor_id = Column(Integer, ForeignKey("utilizatori.id_utilizator", ondelete="RESTRICT"), nullable=False, index=True)
    materie_id = Column(Integer, ForeignKey("materii.id", ondelete="RESTRICT"), nullable=False, index=True)
    data = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    este_motivata = Column(Boolean, default=False, nullable=False, index=True)
    data_motivare = Column(DateTime(timezone=True), nullable=True)
    motiv = Column(String(500), nullable=True)

    elev = relationship("User", foreign_keys=[elev_id], back_populates="absente_primite", lazy="joined")
    profesor = relationship("User", foreign_keys=[profesor_id], lazy="joined")
    materie = relationship("Subject", back_populates="absente", lazy="joined")

class Remark(TimestampMixin, Base):
    __tablename__ = "mentiuni"

    id = Column(Integer, primary_key=True, autoincrement=True)
    elev_id = Column(Integer, ForeignKey("utilizatori.id_utilizator", ondelete="CASCADE"), nullable=False, index=True)
    profesor_id = Column(Integer, ForeignKey("utilizatori.id_utilizator", ondelete="RESTRICT"), nullable=False, index=True)
    tip = Column(String(50), default="MENTIUNE", nullable=False)
    titlu = Column(String(255), nullable=False)
    descriere = Column(Text, nullable=False)
    data = Column(DateTime(timezone=True), default=func.now(), nullable=False)

    elev = relationship("User", foreign_keys=[elev_id], back_populates="mentiuni_primite", lazy="joined")
    profesor = relationship("User", foreign_keys=[profesor_id], lazy="joined")

class Notification(Base):
    __tablename__ = "notificari"

    id = Column(Integer, primary_key=True, autoincrement=True)
    utilizator_id = Column(Integer, ForeignKey("utilizatori.id_utilizator", ondelete="CASCADE"), nullable=False, index=True)
    titlu = Column(String(255), nullable=False)
    mesaj = Column(Text, nullable=False)
    tip = Column(String(50), default="SISTEM", nullable=False)
    este_citita = Column(Boolean, default=False, nullable=False, index=True)
    referinta_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)

    utilizator = relationship("User", back_populates="notificari", lazy="joined")
