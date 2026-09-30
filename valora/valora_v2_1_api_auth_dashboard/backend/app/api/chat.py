from fastapi import APIRouter

router = APIRouter(prefix="/chat", tags=["chat"])

rooms = [
    {
        "id": "general",
        "name": "General",
        "type": "PUBLIC",
    },
    {
        "id": "investment",
        "name": "Investment",
        "type": "PUBLIC",
    },
    {
        "id": "education",
        "name": "Education",
        "type": "PUBLIC",
    },
    {
        "id": "announcements",
        "name": "Announcements",
        "type": "ANNOUNCEMENT",
    },
]


@router.get("/rooms")
def get_rooms():
    return rooms
