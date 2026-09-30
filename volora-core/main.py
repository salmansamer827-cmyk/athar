from fastapi import FastAPI, Depends, HTTPException, Header
from pydantic import BaseModel
import datetime
import secrets
from sqlalchemy.orm import Session
from saas.database.models import SessionLocal, Subscriber, init_db

# تهيئة قاعدة البيانات عند الإقلاع
init_db()

app = FastAPI(
    title="VOL0RA Full SaaS & AI Agent",
    description="Autonomous Multi-tasking SaaS Ecosystem running on Termux",
    version="2.0.0"
)

# Dependency للحصول على جلسة قاعدة البيانات
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# نماذج البيانات (Pydantic Models)
class RegisterRequest(BaseModel):
    username: str
    email: str
    plan: str = "free"

class ServiceRequest(BaseModel):
    query: str

# 1. نقطة حالة النظام العامة
@app.get("/")
def system_status():
    return {
        "agent": "VOL0RA SaaS Core",
        "status": "online",
        "environment": "Termux 24/7 Autonomous Node",
        "time": datetime.datetime.now().isoformat()
    }

# 2. تسجيل عميل SaaS جديد وإعطاؤه مفتاح API خاص به
@app.post("/saas/register")
def register_subscriber(req: RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(Subscriber).filter((Subscriber.username == req.username) | (Subscriber.email == req.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username or Email already registered.")
    
    # توليد مفتاح API فريد للمشترك
    generated_api_key = "vol_" + secrets.token_hex(16)
    
    new_sub = Subscriber(
        username=req.username,
        email=req.email,
        api_key=generated_api_key,
        plan=req.plan,
        is_active=True
    )
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    
    return {
        "status": "success",
        "message": f"Welcome to VOL0RA SaaS, {req.username}!",
        "api_key": generated_api_key,
        "plan": req.plan
    }

# 3. تقديم خدمة الـ SaaS للعملاء المشتركين (محمية بمفتاح API)
@app.post("/saas/consume-service")
def consume_service(req: ServiceRequest, x_api_key: str = Header(...), db: Session = Depends(get_db)):
    # التحقق من صحة المفتاح وحالة الاشتراك
    subscriber = db.query(Subscriber).filter(Subscriber.api_key == x_api_key, Subscriber.is_active == True).first()
    if not subscriber:
        raise HTTPException(status_code=401, detail="Invalid API Key or Inactive Subscription.")
    
    # هنا يتم تنفيذ خدمة الـ SaaS الذكية (مثل تحليل البيانات، التداول، أو معالجة الطلبات)
    result = f"VOL0RA processed query for [{subscriber.username}] under plan [{subscriber.plan}]: '{req.query}'"
    
    return {
        "status": "completed",
        "subscriber": subscriber.username,
        "plan": subscriber.plan,
        "result": result,
        "timestamp": datetime.datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000)
