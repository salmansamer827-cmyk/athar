from sqlalchemy.orm import Session

from app.models import Conversation


def add_message(
    db: Session,
    customer_id: int,
    channel: str,
    direction: str,
    message: str,
):
    if direction not in {
        "INBOUND",
        "OUTBOUND",
    }:
        raise ValueError(
            "direction must be INBOUND or OUTBOUND"
        )

    conversation = Conversation(
        customer_id=customer_id,
        channel=channel,
        direction=direction,
        message=message,
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return conversation


def get_conversation(
    db: Session,
    customer_id: int,
    limit=100
):
    return db.query(Conversation).filter(
        Conversation.customer_id == customer_id
    ).order_by(
        Conversation.created_at.asc()
    ).limit(limit).all()
