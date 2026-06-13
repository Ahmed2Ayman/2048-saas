from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from supabase import create_client, Client

app = FastAPI(title="Lord Kasar System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# بيانات قاعدة البيانات الخاصة بك
SUPABASE_URL = "https://kzuwufstqmqevtphmjhb.supabase.co"
SUPABASE_KEY = "sb_publishable_KKVwrHB_RLoQQv_Mg_ySFw_Sa_ZJix3"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    device_token: str

class VerifyRequest(BaseModel):
    device_token: str

# ----------------- مسارات الـ API (الباك إند) -----------------

@app.post("/api/login")
def login(req: LoginRequest):
    try:
        response = supabase.table("users").select("*").eq("email", req.email).eq("password", req.password).execute()
        if not response.data:
            raise HTTPException(status_code=401, detail="عفواً، البريد الإلكتروني أو كلمة المرور غير صحيحة")
        
        user = response.data[0]
        db_device_token = user.get("device_token")
        
        if not db_device_token:
            supabase.table("users").update({"device_token": req.device_token}).eq("id", user["id"]).execute()
            return {"status": "success", "message": "تم تسجيل الدخول بنجاح وربط جهازك", "device_token": req.device_token}
        
        if db_device_token != req.device_token:
            raise HTTPException(status_code=403, detail="عفواً، هذا الحساب مرتبط بجهاز آخر بالفعل.")
            
        return {"status": "success", "message": "مرحباً بك مجدداً", "device_token": db_device_token}
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/verify")
def verify_token(req: VerifyRequest):
    try:
        response = supabase.table("users").select("*").eq("device_token", req.device_token).execute()
        if not response.data:
            raise HTTPException(status_code=401, detail="جلسة الدخول انتهت.")
        return {"status": "success", "message": "مصرح لك بالدخول"}
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
