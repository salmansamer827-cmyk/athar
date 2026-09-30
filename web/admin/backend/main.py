from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
import datetime
import os

# إعداد قاعدة البيانات محلياً داخل مجلد backend
SQLALCHEMY_DATABASE_URL = "sqlite:///./portfolio.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ProjectModel(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    subtitle = Column(String)
    description = Column(Text)
    category = Column(String)
    cover_image = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class MessageModel(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String)
    message = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Athar Visuals Platform", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ProjectCreate(BaseModel):
    title: str
    subtitle: str
    description: str
    category: str
    cover_image: str

class MessageCreate(BaseModel):
    name: str
    email: str
    message: str

@app.get("/api/projects")
def get_projects(db: Session = Depends(get_db)):
    return db.query(ProjectModel).all()

@app.post("/api/projects", status_code=status.HTTP_201_CREATED)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    db_project = ProjectModel(**project.dict())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return {"message": "Project created successfully", "project": db_project}

@app.post("/api/contact", status_code=status.HTTP_201_CREATED)
def send_message(msg: MessageCreate, db: Session = Depends(get_db)):
    db_msg = MessageModel(**msg.dict())
    db.add(db_msg)
    db.commit()
    db.refresh(db_msg)
    return {"message": "Message sent successfully"}

# ربط واجهة الموقع و لوحة التحكم بناءً على مسار مجلد backend الحالي
@app.get("/")
def serve_web():
    # البحث عن ملف الويب في المجلد المجاور
    path = os.path.abspath("../web/index.html")
    if os.path.exists(path):
        return FileResponse(path)
    return {"message": "Web index.html not found at " + path}

@app.get("/admin")
def serve_admin():
    path = os.path.abspath("../admin/index.html")
    if os.path.exists(path):
        return FileResponse(path)
    return {"message": "Admin index.html not found at " + path}
