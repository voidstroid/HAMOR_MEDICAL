from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# ปลดล็อก CORS ครอบคลุมทุกโดเมน
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ข้อมูลโครงสร้าง (Data Models) ---
class FaceLoginPayload(BaseModel):
    username: str
    image: str

class PasswordLoginPayload(BaseModel):
    username: str
    password: str

class RegisterPayload(BaseModel):
    username: str
    password: str
    fullName: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

# --- 1. พาร์ทสแกนใบหน้า (Face Login) ---
@app.post("/api/auth/login-face")
async def login_face_api(payload: FaceLoginPayload):
    try:
        username = payload.username
        image_base64 = payload.image

        if not username or not image_base64 or "data:image" not in image_base64:
            return {"success": False, "detail": "ข้อมูลชื่อผู้ใช้หรือภาพถ่ายใบหน้าไม่ถูกต้อง"}

        # 🎯 ตรงนี้ใส่โค้ดเช็กใบหน้าของ Gemini AI ได้ตามปกติ
        return {
            "success": True,
            "name": username,
            "user_id": f"PT-{username.upper()}"
        }
    except Exception as e:
        return {"success": False, "detail": str(e)}

# --- 2. พาร์ทล็อกอินด้วยรหัสผ่าน (Password Login) ---
@app.post("/api/auth/login-password")
async def login_password_api(payload: PasswordLoginPayload):
    try:
        username = payload.username
        password = payload.password

        if not username or not password:
            return {"success": False, "detail": "กรุณากรอกชื่อผู้ใช้และรหัสผ่าน"}

        # 🎯 ตัวอย่างจำลองการตรวจสอบรหัสผ่าน (สามารถเชื่อมต่อฐานข้อมูลจริงตรงนี้ได้)
        if username and password: 
            return {
                "success": True,
                "name": username,
                "user_id": f"PT-{username.upper()}"
            }
        else:
            return {"success": False, "detail": "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง"}
    except Exception as e:
        return {"success": False, "detail": str(e)}

# --- 3. พาร์ทสมัครสมาชิก (Register) ---
@app.post("/api/patient/register")
async def register_api(payload: RegisterPayload):
    try:
        if not payload.username or not payload.password:
            return {"success": False, "detail": "กรุณากรอกข้อมูลที่จำเป็นให้ครบถ้วน"}

        # 🎯 ตัวอย่างจำลองการบันทึกข้อมูลคนไข้ใหม่ลงระบบ
        return {
            "success": True,
            "message": "ลงทะเบียนเวชระเบียนคนไข้ใหม่สำเร็จแล้ว!",
            "user_id": f"PT-{payload.username.upper()}"
        }
    except Exception as e:
        return {"success": False, "detail": str(e)}

# --- ดักจับคำขอ Preflight (OPTIONS) ของทุกพาร์ทป้องกัน CORS เออเร่อ ---
@app.options("/api/auth/login-face")
@app.options("/api/auth/login-password")
@app.options("/api/patient/register")
async def options_handler():
    return {"message": "OK"}

@app.get("/api")
async def health_check():
    return {"status": "online", "message": "HAMOR API Gateway is fully operational!"}