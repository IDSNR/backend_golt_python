from fastapi import APIRouter
from data_management.database import check_database_connection

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "partnerhub-python-backend"}


@router.get("/health/database")
def database_health_check() -> dict[str, str]:
    try:
        check_database_connection()
    except Exception:
        return {"status": "unavailable", "service": "postgresql"}
    return {"status": "ok", "service": "postgresql"}
