from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from fastapi import Depends

from app.db.database import get_db
from app.rooms.models import (
    Room,
    RoomMember,
    VoiceSeat,
    MicrophonePermission,
    SpeakingRequest,
)


router = APIRouter(
    prefix="/api/rooms",
    tags=["Rooms"],
)


@router.post("")
def create_room(
    name: str,
    owner_id: int,
    description: str = "",
    max_voice_seats: int = 10,
    db: Session = Depends(get_db),
):
    if max_voice_seats < 1:
        raise HTTPException(
            status_code=400,
            detail="max_voice_seats must be greater than zero",
        )

    room = Room(
        name=name,
        description=description,
        owner_id=owner_id,
        max_voice_seats=max_voice_seats,
    )

    db.add(room)
    db.commit()
    db.refresh(room)

    return {
        "id": room.id,
        "name": room.name,
        "owner_id": room.owner_id,
        "max_voice_seats": room.max_voice_seats,
        "status": "created",
    }


@router.post("/{room_id}/join")
def join_room(
    room_id: int,
    user_id: int,
    db: Session = Depends(get_db),
):
    room = db.query(Room).filter(
        Room.id == room_id,
        Room.is_active == True,
    ).first()

    if not room:
        raise HTTPException(
            status_code=404,
            detail="Room not found",
        )

    existing = db.query(RoomMember).filter(
        RoomMember.room_id == room_id,
        RoomMember.user_id == user_id,
    ).first()

    if existing:
        return {
            "status": "already_joined",
            "room_id": room_id,
            "user_id": user_id,
        }

    member = RoomMember(
        room_id=room_id,
        user_id=user_id,
    )

    db.add(member)
    db.commit()

    return {
        "status": "joined",
        "room_id": room_id,
        "user_id": user_id,
    }


@router.post("/{room_id}/voice-seat/{seat_number}/take")
def take_voice_seat(
    room_id: int,
    seat_number: int,
    user_id: int,
    db: Session = Depends(get_db),
):
    room = db.query(Room).filter(
        Room.id == room_id,
        Room.is_active == True,
    ).first()

    if not room:
        raise HTTPException(
            status_code=404,
            detail="Room not found",
        )

    if seat_number < 1 or seat_number > room.max_voice_seats:
        raise HTTPException(
            status_code=400,
            detail="Invalid voice seat",
        )

    member = db.query(RoomMember).filter(
        RoomMember.room_id == room_id,
        RoomMember.user_id == user_id,
    ).first()

    if not member:
        raise HTTPException(
            status_code=403,
            detail="User is not a room member",
        )

    seat = db.query(VoiceSeat).filter(
        VoiceSeat.room_id == room_id,
        VoiceSeat.seat_number == seat_number,
    ).first()

    if not seat:
        seat = VoiceSeat(
            room_id=room_id,
            seat_number=seat_number,
        )
        db.add(seat)

    if seat.user_id is not None and seat.user_id != user_id:
        raise HTTPException(
            status_code=409,
            detail="Voice seat is occupied",
        )

    permission = db.query(MicrophonePermission).filter(
        MicrophonePermission.room_id == room_id,
        MicrophonePermission.user_id == user_id,
    ).first()

    if not permission or not permission.can_speak:
        raise HTTPException(
            status_code=403,
            detail="Microphone permission required",
        )

    seat.user_id = user_id
    seat.microphone_enabled = False
    seat.is_muted = True

    db.commit()

    return {
        "status": "seat_taken",
        "room_id": room_id,
        "seat_number": seat_number,
        "user_id": user_id,
        "microphone_enabled": False,
        "muted": True,
    }


@router.post("/{room_id}/microphone/{user_id}/grant")
def grant_microphone(
    room_id: int,
    user_id: int,
    granted_by: int,
    db: Session = Depends(get_db),
):
    room = db.query(Room).filter(
        Room.id == room_id,
        Room.owner_id == granted_by,
    ).first()

    if not room:
        raise HTTPException(
            status_code=403,
            detail="Only room owner can grant microphone permission",
        )

    permission = db.query(MicrophonePermission).filter(
        MicrophonePermission.room_id == room_id,
        MicrophonePermission.user_id == user_id,
    ).first()

    if not permission:
        permission = MicrophonePermission(
            room_id=room_id,
            user_id=user_id,
            can_speak=True,
            granted_by=granted_by,
        )
        db.add(permission)
    else:
        permission.can_speak = True
        permission.granted_by = granted_by

    db.commit()

    return {
        "status": "microphone_granted",
        "room_id": room_id,
        "user_id": user_id,
    }


@router.post("/{room_id}/microphone/{user_id}/mute")
def mute_microphone(
    room_id: int,
    user_id: int,
    db: Session = Depends(get_db),
):
    seat = db.query(VoiceSeat).filter(
        VoiceSeat.room_id == room_id,
        VoiceSeat.user_id == user_id,
    ).first()

    if not seat:
        raise HTTPException(
            status_code=404,
            detail="User has no voice seat",
        )

    seat.is_muted = True
    seat.microphone_enabled = False

    db.commit()

    return {
        "status": "muted",
        "room_id": room_id,
        "user_id": user_id,
    }


@router.post("/{room_id}/speaking-request")
def request_to_speak(
    room_id: int,
    user_id: int,
    db: Session = Depends(get_db),
):
    request = SpeakingRequest(
        room_id=room_id,
        user_id=user_id,
        status="pending",
    )

    db.add(request)
    db.commit()
    db.refresh(request)

    return {
        "status": "pending",
        "request_id": request.id,
        "room_id": room_id,
        "user_id": user_id,
    }
@router.get("")
def list_rooms(
    db: Session = Depends(get_db),
):
    rooms = (
        db.query(Room)
        .filter(Room.is_active == True)
        .order_by(Room.created_at.desc())
        .all()
    )

    return {
        "rooms": [
            {
                "id": room.id,
                "name": room.name,
                "description": room.description,
                "owner_id": room.owner_id,
                "max_voice_seats": room.max_voice_seats,
            }
            for room in rooms
        ]
    }
