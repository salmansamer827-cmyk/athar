from sqlalchemy.orm import Session

from app.models import Lead


VALID_STATUSES = {
    "NEW",
    "CONTACTED",
    "REPLIED",
    "INTERESTED",
    "NEGOTIATING",
    "PAYMENT_PENDING",
    "PAID",
    "ACTIVE",
    "EXPIRED",
    "RENEWAL_PENDING",
    "CLOSED",
}


def create_lead(
    db: Session,
    name=None,
    email=None,
    phone=None,
    telegram_username=None,
    source=None,
    profile_url=None,
    notes=None,
):
    lead = Lead(
        name=name,
        email=email,
        phone=phone,
        telegram_username=telegram_username,
        source=source,
        profile_url=profile_url,
        notes=notes,
        status="NEW",
    )

    db.add(lead)
    db.commit()
    db.refresh(lead)

    return lead


def get_lead(db: Session, lead_id: int):
    return db.query(Lead).filter(
        Lead.id == lead_id
    ).first()


def update_lead_status(
    db: Session,
    lead_id: int,
    status: str
):
    status = status.upper()

    if status not in VALID_STATUSES:
        raise ValueError(
            f"Invalid lead status: {status}"
        )

    lead = get_lead(db, lead_id)

    if not lead:
        raise ValueError("Lead not found")

    lead.status = status

    db.commit()
    db.refresh(lead)

    return lead


def list_leads(
    db: Session,
    status=None,
    limit=100
):
    query = db.query(Lead)

    if status:
        query = query.filter(
            Lead.status == status.upper()
        )

    return query.order_by(
        Lead.created_at.desc()
    ).limit(limit).all()
