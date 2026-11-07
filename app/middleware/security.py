import ipaddress
import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger("security")

MAX_REQUEST_BODY_SIZE = 10 * 1024 * 1024

EXCLUDED_DOCS_PATHS = (
    "/docs",
    "/redoc",
    "/openapi.json",
    "/health",
    "/",
)

DOCS_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "img-src 'self' data: https://fastapi.tiangolo.com; "
    "connect-src 'self' http://localhost:8000 http://127.0.0.1:8000;"
)

API_CSP = "default-src 'none'"

SECURITY_HEADERS = {
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
}

def get_client_ip(request: Request) -> str:
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()

    client_conn_ip = request.headers.get("x-real-ip")
    if client_conn_ip:
        return client_conn_ip.strip()

    return request.client.host if request.client else "unknown"

async def security_middleware(request: Request, call_next):
    path = request.url.path
    is_docs_path = any(path.startswith(p) for p in EXCLUDED_DOCS_PATHS)

    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > MAX_REQUEST_BODY_SIZE:
                return JSONResponse(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    content={"detail": "Dimensiunea cererii depaseste limita permisa de 10MB."},
                )
        except ValueError:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Header-ul Content-Length este invalid."},
            )

    accept_header = request.headers.get("accept", "*/*")
    if not is_docs_path and "*/*" not in accept_header and "application/json" not in accept_header:
        return JSONResponse(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            content={"detail": "API-ul accepta doar raspunsuri in format application/json."},
        )

    response = await call_next(request)

    for header_name, header_value in SECURITY_HEADERS.items():
        response.headers[header_name] = header_value

    response.headers["Content-Security-Policy"] = DOCS_CSP if is_docs_path else API_CSP

    if "server" in response.headers:
        del response.headers["server"]
    if "x-powered-by" in response.headers:
        del response.headers["x-powered-by"]

    return response
