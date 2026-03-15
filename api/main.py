from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from supabase import create_client, Client

app = FastAPI()

# إعدادات الأمان
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = "https://kzuwufstqmqevtphmjhb.supabase.co"
SUPABASE_KEY = "sb_publishable_KKVwrHB_RLoQQv_Mg_ySFw_Sa_ZJix3"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ----------------- نماذج البيانات -----------------
class LoginRequest(BaseModel):
    email: str
    password: str
    device_token: str # هنا السيرفر هيستقبل بصمة الجهاز من الواجهة

class VerifyRequest(BaseModel):
    device_token: str

# ----------------- مسارات الـ API -----------------

@app.get("/")
def read_root():
    return {"message": "السيرفر شغال وزي الفل!"}

@app.post("/api/login")
def login(req: LoginRequest):
    response = supabase.table("users").select("*").eq("email", req.email).eq("password", req.password).execute()
    
    if not response.data:
        raise HTTPException(status_code=401, detail="الإيميل أو الباسورد غير صحيح")
    
    user = response.data[0]
    db_device_token = user.get("device_token")
    
    # لو اليوزر بيدخل لأول مرة (مفيش بصمة متسجلة ليه)
    if not db_device_token:
        # هنسجل بصمة الجهاز اللي باعتها في الداتا بيز
        supabase.table("users").update({"device_token": req.device_token}).eq("id", user["id"]).execute()
        return {
            "status": "success", 
            "message": "تم تسجيل الدخول وربط الحساب بجهازك بنجاح", 
            "device_token": req.device_token
        }
    
    # لو في بصمة متسجلة، هنقارنها بالبصمة الحالية للجهاز
    if db_device_token != req.device_token:
        raise HTTPException(status_code=403, detail="عفواً، هذا الحساب مرتبط بجهاز آخر. تواصل مع الإدارة.")
        
    return {
        "status": "success", 
        "message": "مرحباً بك مجدداً", 
        "device_token": db_device_token
    }

@app.post("/api/verify")
def verify_token(req: VerifyRequest):
    response = supabase.table("users").select("*").eq("device_token", req.device_token).execute()
    
    if not response.data:
        raise HTTPException(status_code=401, detail="غير مصرح بالدخول من هذا الجهاز")
    
    return {"status": "success", "message": "مصرح له بالدخول"}
