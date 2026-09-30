from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from app.database import (
    get_db,
    init_db,
)

from app.config import settings
from app.leads import (
    create_lead,
    list_leads,
)

from app.sales_agent import sales_agent


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/product")
def product():
    return sales_agent.product_summary()


@app.post("/leads")
def add_lead(
    name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    telegram_username: str | None = None,
    source: str | None = None,
    profile_url: str | None = None,
    notes: str | None = None,
    db: Session = Depends(get_db),
):
    lead = create_lead(
        db=db,
        name=name,
        email=email,
        phone=phone,
        telegram_username=telegram_username,
        source=source,
        profile_url=profile_url,
        notes=notes,
    )

    return {
        "id": lead.id,
        "status": lead.status,
        "name": lead.name,
    }


@app.get("/leads")
def get_leads(
    status: str | None = None,
    db: Session = Depends(get_db),
):
    leads = list_leads(
        db=db,
        status=status,
    )

    return [
        {
            "id": lead.id,
            "name": lead.name,
            "email": lead.email,
            "phone": lead.phone,
            "telegram_username":
                lead.telegram_username,
            "source": lead.source,
            "status": lead.status,
            "created_at": lead.created_at,
        }
        for lead in leads
    ]


@app.post("/agent/answer")
def agent_answer(message: str):
    return {
        "agent": settings.AGENT_NAME,
        "response": sales_agent.answer(
            message
        ),
    }
