from fastapi import APIRouter

# Create router object
router = APIRouter()

# Example test route
@router.get("/")
def get_users():
    return {"message": "Users route working!"}
