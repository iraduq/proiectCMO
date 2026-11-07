from typing import Any, Optional
from starlette import status
from app.utils.custom_exception import AppException

class RequestValidationError(AppException):
    def __init__(self, errors: list[dict[str, Any]]) -> None:
        super().__init__(
            message="Datele transmise contin campuri invalide.",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="validation_error",
            details=errors,
        )

class PasswordValidationError(AppException):
    def __init__(self) -> None:
        super().__init__(
            message="Parola trebuie sa contina cel putin 8 caractere, majuscule, litere mici, cifre si un simbol special.",
            status_code=status.HTTP_400_BAD_REQUEST,
            code="invalid_password",
        )

class InvalidCredentialsError(AppException):
    def __init__(self) -> None:
        super().__init__(
            message="Adresa de email sau parola incorecta.",
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="invalid_credentials",
        )

class InvalidTokenError(AppException):
    def __init__(self) -> None:
        super().__init__(
            message="Token de autentificare invalid sau expirat.",
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="invalid_token",
        )

class UnauthorizedAccessError(AppException):
    def __init__(self, detail: str = "Nu aveti permisiunile necesare pentru a efectua aceasta actiune.") -> None:
        super().__init__(
            message=detail,
            status_code=status.HTTP_403_FORBIDDEN,
            code="forbidden_access",
        )

class UserEmailAlreadyExistsError(AppException):
    def __init__(self, email: str) -> None:
        super().__init__(
            message=f"Adresa de email '{email}' este deja inregistrata in catalog.",
            status_code=status.HTTP_409_CONFLICT,
            code="user_email_already_exists",
        )

class UserNotFoundError(AppException):
    def __init__(self, identifier: Optional[Any] = None) -> None:
        message = (
            f"Utilizatorul cu identificatorul '{identifier}' nu a fost gasit."
            if identifier
            else "Utilizatorul nu a fost gasit."
        )
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            code="user_not_found",
        )

class ClassNotFoundError(AppException):
    def __init__(self, class_id: int) -> None:
        super().__init__(
            message=f"Clasa cu ID-ul {class_id} nu a fost gasita.",
            status_code=status.HTTP_404_NOT_FOUND,
            code="class_not_found",
        )

class SubjectNotFoundError(AppException):
    def __init__(self, subject_id: int) -> None:
        super().__init__(
            message=f"Materia cu ID-ul {subject_id} nu a fost gasita.",
            status_code=status.HTTP_404_NOT_FOUND,
            code="subject_not_found",
        )

class GradeNotFoundError(AppException):
    def __init__(self, grade_id: int) -> None:
        super().__init__(
            message=f"Nota cu ID-ul {grade_id} nu a fost gasita.",
            status_code=status.HTTP_404_NOT_FOUND,
            code="grade_not_found",
        )

class InvalidGradeValueError(AppException):
    def __init__(self, valoare: int) -> None:
        super().__init__(
            message=f"Nota trebuie sa fie o valoare intre 1 si 10. Valoarea furnizata: {valoare}.",
            status_code=status.HTTP_400_BAD_REQUEST,
            code="invalid_grade_value",
        )

class AbsenceNotFoundError(AppException):
    def __init__(self, absence_id: int) -> None:
        super().__init__(
            message=f"Absenta cu ID-ul {absence_id} nu a fost gasita.",
            status_code=status.HTTP_404_NOT_FOUND,
            code="absence_not_found",
        )

class RemarkNotFoundError(AppException):
    def __init__(self, remark_id: int) -> None:
        super().__init__(
            message=f"Mentiunea cu ID-ul {remark_id} nu a fost gasita.",
            status_code=status.HTTP_404_NOT_FOUND,
            code="remark_not_found",
        )

class ParentChildLinkError(AppException):
    def __init__(self, detail: str = "Elevul nu este asociat contului dumneavoastra de parinte.") -> None:
        super().__init__(
            message=detail,
            status_code=status.HTTP_403_FORBIDDEN,
            code="parent_child_not_linked",
        )

class NotificationNotFoundError(AppException):
    def __init__(self, notification_id: int) -> None:
        super().__init__(
            message=f"Notificarea cu ID-ul {notification_id} nu a fost gasita.",
            status_code=status.HTTP_404_NOT_FOUND,
            code="notification_not_found",
        )

class DataIntegrityError(AppException):
    def __init__(self, detail: str = "A aparut un conflict de integritate a datelor.") -> None:
        super().__init__(
            message=detail,
            status_code=status.HTTP_409_CONFLICT,
            code="data_integrity_conflict",
        )
