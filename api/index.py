from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# ปลดล็อกกำแพง CORS แบบสากลรองรับทุก Origin ข้ามโดเมน
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- โครงสร้างข้อมูล (Data Models) ---
class FaceLoginPayload(BaseModel):
    username: str
    image: str

class PasswordLoginPayload(BaseModel):
    username: str
    password: str

class RegisterPayload(BaseModel):
    username: str
    password: str

class UpdateStatusPayload(BaseModel):
    patient_id: str
    status: str

class AIDiagnosisPayload(BaseModel):
    patient_id: str
    symptoms: str
    medical_history: Optional[str] = "ไม่มี"

# --- 1. ระบบล็อกอินด้วยใบหน้า / รหัสผ่าน / สมัครสมาชิก ---
@app.post("/api/auth/login-face")
async def login_face_api(payload: FaceLoginPayload):
    return {"success": True, "name": payload.username, "user_id": f"PT-{payload.username.upper()}"}

@app.post("/api/auth/login-password")
async def login_password_api(payload: PasswordLoginPayload):
    return {"success": True, "name": payload.username, "user_id": f"PT-{payload.username.upper()}"}

@app.post("/api/patient/register")
async def register_api(payload: RegisterPayload):
    return {"success": True, "message": "ลงทะเบียนสำเร็จ", "user_id": f"PT-{payload.username.upper()}"}

# --- 2. ระบบข้อมูลแดชบอร์ดหลักคนไข้ (Dashboard Data) ---
@app.get("/api/patient/dashboard/{patient_id}")
async def get_dashboard_data(patient_id: str):
    # จำลองการดึงเวชระเบียนจากฐานข้อมูลหลักมาแสดงผล
    return {
        "success": True,
        "patient_id": patient_id,
        "vital_signs": {"blood_pressure": "120/80", "heart_rate": 78, "temperature": 36.6},
        "appointments": [{"date": "2026-06-20", "doctor": "นพ. สมชาย (อายุรกรรม)", "time": "10:00"}],
        "message": "ดึงข้อมูลเวชระเบียน CareSync Engine สำเร็จ"
    }

# --- 3. ระบบสถานะออนไลน์ & ประวัติโทรเวชกรรม (Telehealth & Chat) ---
@app.post("/api/telehealth/update-status")
async def update_status_api(payload: UpdateStatusPayload):
    return {"success": True, "status": payload.status, "patient_id": payload.patient_id}

@app.get("/api/telehealth/history")
async def get_chat_history(patient_id: str):
    return {
        "success": True,
        "patient_id": patient_id,
        "history": [
            {"sender": "system", "message": "ยินดีต้อนรับเข้าสู่ระบบห้องตรวจออนไลน์ HAMOR Telehealth", "time": "09:00"},
            {"sender": "doctor", "message": "สวัสดีครับคนไข้ วันนี้มีอาการผิดปกติอย่างไรบ้างครับ?", "time": "09:01"}
        ]
    }

# --- 4. ระบบสมองกลคัดกรองโรคอัตโนมัติด้วย AI (AI Diagnosis) ---
@app.post("/api/patient/ai-diagnosis")
async def ai_diagnosis_api(payload: AIDiagnosisPayload):
    try:
        if not payload.symptoms:
            return {"success": False, "detail": "กรุณาระบุอาการเพื่อส่งให้ AI วิเคราะห์"}
        
        return {
            "success": True,
            "analysis": {
                "possible_condition": "กลุ่มอาการอ่อนเพลียและติดเชื้อทางเดินหายใจเบื้องต้น",
                "risk_level": "Low-Medium",
                "ai_recommendation": "พักผ่อนให้เพียงพอ ดื่มน้ำสะอาดปริมาณมาก หากมีอาการไข้สูงเกิน 3 วันโปรดนัดพบแพทย์"
            }
        }
    except Exception as e:
        return {"success": False, "detail": str(e)}

# --- ปลดล็อกสิทธิ์ Preflight (OPTIONS) ครอบคลุมทุกเส้นทางป้องกัน CORS พัง ---
@app.options("/{rest_of_path:path}")
async def preflight_handler(rest_of_path: str):
    return {"message": "OK"}

@app.get("/api")
async def root_check():
    return {"status": "online", "message": "HAMOR API Gateway V2 Operational"}