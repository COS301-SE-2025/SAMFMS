from fastapi import APIRouter

# Create the main router instance
router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "ok", "service": "vehicles"}