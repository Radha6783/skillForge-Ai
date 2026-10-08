from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from app.database import get_db, engine

router = APIRouter(prefix="/api/health", tags=["Health"])

@router.get("", status_code=status.HTTP_200_OK)
@router.get("/", status_code=status.HTTP_200_OK)
def get_health():
    return {
        "status": "healthy",
        "message": "SkillForge AI Backend API is operational",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "1.0.0"
    }

@router.get("/db", status_code=status.HTTP_200_OK)
def get_db_health(db: Session = Depends(get_db)):
    try:
        # Execute simple query to test DB connection
        result = db.execute(text("SELECT 1")).scalar()
        if result == 1:
            db_driver = engine.dialect.name
            return {
                "status": "healthy",
                "database": "connected",
                "engine": db_driver,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database returned unexpected response"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database connection failed: {str(e)}"
        )
