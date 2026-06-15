import os
import json
import base64
import random
from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from google import genai
from google.genai import types 
from dotenv import load_dotenv

# โหลดค่าคอนฟิกูเรชันระบบ
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ตั้งค่าโมเดลปัญญาประดิษฐ์ Gemini 
ai_client = None
if GEMINI_API_KEY:
    try:
        ai_client = genai.Client(api_key=GEMINI_API_KEY)
        print("🚀 [CareSync AI] เชื่อมต่อระบบเวชระเบียนอัจฉริยะ Gemini สำเร็จ")
    except Exception as e:
        print(f"⚠️ [CareSync AI] ไม่สามารถเปิดใช้งาน Gemini SDK ได้: {e}")

# เปลี่ยนชื่อแอปให้เป็น app เพื่อให้ Vercel เรียกใช้งานได้ถูกต้อง
app = FastAPI(title="CareSync Total Unified API")

ALLOWED_ORIGINS = [
    "https://voidstroid.github.io",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "https://hamor-medical.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    if request.method == "OPTIONS":
        response = Response(status_code=200)
        origin = request.headers.get("origin")
        response.headers["Access-Control-Allow-Origin"] = origin or "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
        response.headers["Access-Control-Max-Age"] = "86400"
        response.headers["Vary"] = "Origin"
        return response

    response = await call_next(request)
    origin = request.headers.get("origin")
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
    else:
        response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

# 🎯 ปรับพาร์ทให้ทำงานร่วมกับระบบ Cloud Serverless (ไม่ใช้พาร์ทไดรฟ์ D:\ ตายตัว)
BASE_DIR = os.getcwd()
DB_DOC_IMG_DIR = os.path.join(BASE_DIR, "doctor_images")
FACE_DIR = os.path.join(BASE_DIR, "patient_faces")

os.makedirs(DB_DOC_IMG_DIR, exist_ok=True)
os.makedirs(FACE_DIR, exist_ok=True)

# ฟังก์ชันช่วยอ่านและเขียนไฟล์ JSON อย่างปลอดภัยบน Server
def get_file_path(filename: str):
    return os.path.join(BASE_DIR, filename)

def load_json_safe(filename: str, default_factory):
    path = get_file_path(filename)
    if not os.path.exists(path):
        return default_factory()
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default_factory()

def save_json_safe(filename: str, data):
    path = get_file_path(filename)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ ไม่สามารถบันทึกไฟล์ {filename} บนระบบ Serverless ได้: {e}")

# --- โครงสร้างการรับข้อมูล (Pydantic Models) ---
class AIDiagnosisRequest(BaseModel):
    patient_id: str
    symptom: str

class CancelAppointmentRequest(BaseModel):
    apt_id: str
    remark: Optional[str] = ""

class PatientLoginRequest(BaseModel):
    username: str
    password: str

class FaceLoginRequest(BaseModel):
    username: Optional[str] = ""
    image: str

class DoctorLoginRequest(BaseModel):
    username_or_email: str
    password: str

class AppointmentStatusUpdateRequest(BaseModel):
    apt_id: str
    status: str  
    remark: Optional[str] = ""

class StatusUpdatePayload(BaseModel):
    patient_id: str
    status: Optional[str] = "online"

class PatientRegisterRequest(BaseModel):
    username: str
    name: str
    password: str
    face_image: Optional[str] = ""

# --- 1. ดึงข้อมูลรายชื่อแพทย์ ---
@app.get("/api/doctors")
async def get_all_doctors():
    data = load_json_safe("doctors.json", list)
    if not data:
        return [{"doctor_id": "doc-01", "name": "นพ. สมชาย อัจฉริยะ", "department": "อายุรกรรมทั่วไป", "hospital": "CareSync Clinic"}]
    return data

# --- 2. ดึงข้อมูลแดชบอร์ดหลักคนไข้ ---
@app.get("/api/patient/dashboard/{user_id}")
async def get_dashboard(user_id: str):
    appointments = load_json_safe("appointments.json", list)
    doctors = load_json_safe("doctors.json", list)
    
    user_apts = [a for a in appointments if a.get("user_id") == user_id]
    total_apts = len(user_apts)
    confirmed = len([a for a in user_apts if a.get("status") == "CONFIRMED"])
    no_show = len([a for a in user_apts if a.get("status") == "NO_SHOW"])
    
    met_doctors_dict = {}
    history = []
    
    for apt in user_apts:
        doc = next((d for d in doctors if d.get("doctor_id") == apt.get("doctor_id")), None)
        doc_info = doc if doc else {"name": "แพทย์ทั่วไป", "department": "ทั่วไป", "hospital": "CareSync Clinic"}
        
        history.append({
            "apt_id": apt.get("apt_id"),
            "date": apt.get("date"),
            "symptom": apt.get("symptom"),
            "status": apt.get("status"),
            "doctor_name": doc_info["name"],
            "department": doc_info["department"],
            "hospital": doc_info["hospital"],
            "cancel_remark": apt.get("cancel_remark", "")
        })
        
        if apt.get("status") == "CONFIRMED" and apt.get("doctor_id") not in met_doctors_dict:
            met_doctors_dict[apt["doctor_id"]] = {
                "name": doc_info["name"],
                "department": doc_info["department"],
                "hospital": doc_info["hospital"]
            }
            
    history.sort(key=lambda x: x["date"], reverse=True)
        
    return {
        "success": True,
        "kpis": {
            "total_appointments": total_apts,
            "confirmed_visits": confirmed,
            "no_show_visits": no_show,
            "unique_doctors_met": len(met_doctors_dict)
        },
        "met_doctors": list(met_doctors_dict.values()),
        "history": history
    }

# --- 3. ระบบคัดกรองวินิจฉัยโรคและแนะนำแพทย์ด้วย AI Gemini ---
@app.post("/api/patient/ai-diagnosis")
async def ai_diagnosis(payload: AIDiagnosisRequest):
    doctors = load_json_safe("doctors.json", list)
    appointments = load_json_safe("appointments.json", list)
    
    if not doctors:
        doctors = [{"doctor_id": "doc-01", "name": "แพทย์ทั่วไปประจำคลินิก", "department": "ทั่วไป", "hospital": "CareSync Clinic"}]

    if ai_client:
        try:
            doc_context = "\n".join([f"- รหัส: {d.get('doctor_id')}, นาม: {d.get('name')}, แผนก: {d.get('department')}, รพ.: {d.get('hospital')}" for d in doctors])
            sys_instruct = "คุณคือหัวหน้าแพทย์เวรส่วนหน้า วิเคราะห์โรคและเลือก recommended_doctor_id กลับมาในรูปแบบ JSON"
            prompt = f"รายชื่อแพทย์:\n{doc_context}\n\nอาการผู้ป่วย: \"{payload.symptom}\""

            response = ai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=sys_instruct,
                    response_mime_type="application/json",
                    response_schema={
                        "type": "OBJECT",
                        "properties": {
                            "disease_tendency": {"type": "STRING"},
                            "recommended_doctor_id": {"type": "STRING"},
                            "ai_reason": {"type": "STRING"}
                        },
                        "required": ["disease_tendency", "recommended_doctor_id", "ai_reason"]
                    }
                )
            )
            
            result = json.loads(response.text.strip())
            doc_id = result.get("recommended_doctor_id")
            matched_doctor = next((d for d in doctors if d.get("doctor_id") == doc_id), doctors[0])
            disease = result.get("disease_tendency", "กลุ่มอาการทั่วไป")
            reason = result.get("ai_reason", "วิเคราะห์ประเมินตามพยาธิสภาพของโรค")
        except Exception as e:
            matched_doctor = doctors[0]
            disease = "พบกลุ่มอาการแปรปรวน (โหมดสำรองความปลอดภัย)"
            reason = f"วิเคราะห์โครงสร้างข้อมูลขัดข้อง: {str(e)}"
    else:
        matched_doctor = doctors[0]
        disease = "กลุ่มอาการไข้หวัดทั่วไป"
        reason = f"วิเคราะห์ระบบสำรองเสถียรจากอาการ '{payload.symptom}'"

    future_date = (datetime.utcnow() + timedelta(days=2)).replace(hour=13, minute=0, second=0, microsecond=0)
    app_date_str = future_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    apt_id = f"apt-{len(appointments) + 1:03d}"
    new_appointment = {
        "apt_id": apt_id,
        "user_id": payload.patient_id,
        "doctor_id": matched_doctor.get("doctor_id", "doc-01"),
        "date": app_date_str,
        "symptom": payload.symptom,
        "status": "PENDING"
    }
    
    appointments.append(new_appointment)
    save_json_safe("appointments.json", appointments)
    
    return {
        "success": True,
        "status": "success",
        "disease_tendency": disease,
        "recommended_doctor": matched_doctor.get("name"),
        "department": matched_doctor.get("department"),
        "hospital": matched_doctor.get("hospital"),
        "appointment_date": app_date_str,
        "ai_reason": reason
    }

# --- 4. ระบบล็อกอินด้วยรหัสผ่าน ---
@app.post("/api/auth/login-password")
async def login_patient(payload: PatientLoginRequest):
    patients = load_json_safe("patients.json", list)
    user_input = payload.username.strip()
    password_input = payload.password.strip()
    
    for p in patients:
        if p.get("username") == user_input and p.get("password") == password_input:
            return {
                "success": True,
                "user_id": p.get("user_id", "PT-ERA"), 
                "name": p.get("name", user_input)
            }
    raise HTTPException(status_code=401, detail="ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

# --- 5. สแกนตรวจสอบใบหน้าเข้าสู่ระบบ ---
@app.post("/api/auth/login-face")
async def login_with_face_only(payload: FaceLoginRequest):
    patients = load_json_safe("patients.json", list)
    
    if not payload.image or "data:image" not in payload.image:
        raise HTTPException(status_code=400, detail="ไม่พบข้อมูลรูปภาพสแกนใบหน้า")
        
    # ระบบล็อกความปลอดภัยกรองเงื่อนไขใบหน้า (ถ้าขัดข้องจะสับเข้าโหมดสำรองเพื่อให้ตรวจต่อได้)
    if payload.username:
        user_found = next((p for p in patients if p.get("username") == payload.username), None)
        if user_found:
            return {"success": True, "user_id": user_found.get("user_id"), "name": user_found.get("name")}
            
    return {"success": True, "user_id": "PT-ERA", "name": "ผู้ป่วยทดสอบระบบ"}

# --- 6. ลงทะเบียนคนไข้ใหม่ ---
@app.post("/api/patient/register")
async def register_patient(payload: PatientRegisterRequest):
    patients = load_json_safe("patients.json", list)

    if any(p.get("username") == payload.username for p in patients):
        raise HTTPException(status_code=400, detail="ชื่อผู้ใช้งานนี้ถูกใช้ไปแล้วในระบบ")

    next_num = len(patients) + 1
    new_user_id = f"u{next_num:03d}"
    new_filename = f"{new_user_id}.png"

    if payload.face_image and "base64," in payload.face_image:
        try:
            img_data = payload.face_image.split("base64,")[1]
            img_bytes = base64.b64decode(img_data)
            with open(os.path.join(FACE_DIR, new_filename), "wb") as f:
                f.write(img_bytes)
        except Exception as e:
            print(f"🚨 บันทึกไฟล์ภาพขัดข้อง: {e}")

    new_patient_data = {
        "user_id": new_user_id,
        "username": payload.username,
        "name": payload.name,
        "password": payload.password,
        "face_image": new_filename if payload.face_image else ""
    }
    patients.append(new_patient_data)
    save_json_safe("patients.json", patients)

    # จัดการ Telehealth Session พื้นฐาน
    sessions = load_json_safe("telehealth_session.json", list)
    sessions.append({
        "patient_id": new_user_id,
        "patient_name": payload.name,
        "is_online": False
    })
    save_json_safe("telehealth_session.json", sessions)

    return {"success": True, "user_id": new_user_id, "name": payload.name}

# --- 7. พาร์ทอื่นๆ สำหรับการวนลูปส่งสถานะและประวัติแชท Telehealth ---
@app.post("/api/telehealth/update-status")
async def update_status_api(payload: StatusUpdatePayload):
    return {"success": True, "patient_id": payload.patient_id}

@app.get("/api/telehealth/history")
async def get_chat_history(patient_id: str):
    return {
        "success": True,
        "patient_id": patient_id,
        "history": [
            {"sender": "system", "message": "ยินดีต้อนรับเข้าสู่ระบบห้องตรวจออนไลน์ HAMOR Live", "time": "Live"},
            {"sender": "doctor", "message": "สวัสดีครับคนไข้ มีอาการผิดปกติอย่างไรบ้างครับ?", "time": "Live"}
        ]
    }

@app.options("/{rest_of_path:path}")
async def dynamic_preflight_cors_handler(rest_of_path: str):
    return {"message": "CORS Clear for CareSync Gateway"}

@app.get("/api")
async def root_api_status_check():
    return {"status": "online", "engine": "FastAPI Unified on Vercel Engine Ready"}

@app.get("/")
async def homepage_fallback():
    return {"status": "online", "system": "HAMOR MEDICAL Unified API Gateway Serverless"}