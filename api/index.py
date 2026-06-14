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

# --- ข้อมูลโครงสร้างสำหรับระบบคัดกรองโรค (Symptom Screening Model) ---
class ScreeningPayload(BaseModel):
    patient_id: str
    symptoms: str          # อาการที่คนไข้พิมพ์เข้ามา
    medical_history: Optional[str] = "ไม่มี" # ประวัติโรคประจำตัว
    vital_signs: Optional[dict] = None     # เช่น ความดัน อุณหภูมิ (ถ้ามี)

# --- 4. พาร์ทตรวจคัดกรองโรคอัตโนมัติด้วย AI ---
@app.post("/api/telehealth/ai-screening")
async def ai_screening_api(payload: ScreeningPayload):
    try:
        if not payload.symptoms:
            return {"success": False, "detail": "กรุณาระบุอาการที่ต้องการให้ AI วิเคราะห์"}

        # 🎯 ตรงนี้คือจุดเชื่อมต่อ Gemini API หรือ LLM ของคุณ
        # ตัวอย่างโครงสร้างการส่ง Prompt ให้ AI วิเคราะห์:
        # ai_prompt = f"คนไข้อาการ: {payload.symptoms}, ประวัติ: {payload.medical_history}"
        
        # 🤖 จำลองผลลัพธ์ที่ AI คัดกรองและสรุปกลับมา (Mock AI Insights)
        ai_analysis = {
            "possible_condition": "กลุ่มอาการติดเชื้อในระบบทางเดินหายใจส่วนบน (อาจเป็นไข้หวัดใหญ่)",
            "risk_level": "Medium", # Low, Medium, High
            "urgency": "ควรพบแพทย์ภายใน 24-48 ชั่วโมง หรือรับยาตามอาการ",
            "ai_recommendation": "แนะนำให้พักผ่อนอย่างเพียงพอ ดื่มน้ำอุ่น และทานยาลดไข้ตามอาการ หากมีอาการหายใจหอบเหนื่อยให้รีบพบแพทย์ทันที"
        }

        return {
            "success": True,
            "patient_id": payload.patient_id,
            "analysis": ai_analysis
        }
    except Exception as e:
        return {"success": False, "detail": str(e)}

# --- ดักจับคำขอ Preflight (OPTIONS) ป้องกัน CORS ให้พาร์ท AI ---
@app.options("/api/telehealth/ai-screening")
async def options_ai_screening():
    return {"message": "OK"}