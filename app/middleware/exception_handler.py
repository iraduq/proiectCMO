from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError as FastAPIValidationError
from fastapi.responses import JSONResponse
from app.utils.custom_exception import AppException

def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        content = {
            "detail": exc.message,
            "code": exc.code,
        }
        if exc.details is not None:
            content["details"] = jsonable_encoder(exc.details)
        return JSONResponse(status_code=exc.status_code, content=content)

    @app.exception_handler(FastAPIValidationError)
    async def validation_exception_handler(request: Request, exc: FastAPIValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content=jsonable_encoder(
                {
                    "detail": "Datele transmise contin erori de validare.",
                    "code": "validation_error",
                    "details": exc.errors(),
                }
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "detail": "A aparut o eroare interna de procesare.",
                "code": "internal_server_error",
            },
        )
