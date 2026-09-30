from sqlalchemy.orm import Session

from app.models import Customer, Lead


def create_customer_from_lead(
    db: Session,
    lead: Lead
):
    existing = db.query(Customer).filter(
        Customer.lead_id == lead.id
    ).first()

    if existing:
        return existing

    customer = Customer(
        lead_id=lead.id,
        name=lead.name,
        email=lead.email,
        phone=lead.phone,
        telegram_username=lead.telegram_username,
        status="INTERESTED",
    )

    db.add(customer)

    lead.status = "INTERESTED"

    db.commit()
    db.refresh(customer)

    return customer


def get_customer(
    db: Session,
    customer_id: int
):
    return db.query(Customer).filter(
        Customer.id == customer_id
    ).first()


def update_customer_status(
    db: Session,
    customer_id: int,
    status: str
):
    customer = get_customer(
        db,
        customer_id
    )

    if not customer:
        raise ValueError(
            "Customer not found"
        )

    customer.status = status.upper()

    db.commit()
    db.refresh(customer)

    return customer
