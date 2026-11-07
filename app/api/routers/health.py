from fastapi import APIRouter

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "EduGrade Digital Gradebook API",
        "version": "1.0.0",
        "cloud_ready": "true",
    }
