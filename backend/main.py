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
        print("🚀 [HAMOR AI] เชื่อมต่อระบบเวชระเบียนอัจฉริยะ Gemini สำเร็จ")
    except Exception as e:
        print(f"⚠️ [HAMOR AI] ไม่สามารถเปิดใช้งาน Gemini SDK ได้: {e}")

app = FastAPI(title="HAMOR Total Unified API")

# 1. ระบุชื่อโดเมนหน้าบ้านของคุณให้ชัดเจน (หรือใส่ "*" เพื่อเปิดรับทั้งหมด)
origins = [
    "https://voidstroid.github.io",
    "http://localhost:5500",  # สำหรับเวลาคุณเปิดทดสอบในเครื่องตัวเอง (Live Server)
    "http://127.0.0.1:5500",
]

# 2. ตั้งค่าการเคลียร์ปลดล็อกสิทธิ์ให้เข้าถึงได้จากภายนอก

# ปลดล็อก CORS ด่านที่ 1 (FastAPI Level)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False, # ต้องเป็น False หากใช้ originsเป็น "*"
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🎯 2. เพิ่มสคริปต์นี้เข้าไป: ดักจับและบังคับตอบกลับ 200 OK ทันทีหากหน้าบ้านยิง OPTIONS เข้ามา เช็กก่อนเข้าถึงฟังก์ชันหลัก
@app.middleware("http")
async def cors_preflight_middleware(request: Request, call_next):
    # ถ้าหน้าบ้านส่งคำสั่งเช็กประตู (OPTIONS) เข้ามา
    if request.method == "OPTIONS":
        response = Response(status_code=200)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
        return response
    
    # ถ้าเป็นคำสั่งปกติ (เช่น POST ภาพสแกนใบหน้า) ให้ปล่อยไหลไปทำงานตามปกติ
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

@app.post("/api/auth/login-face")
async def login_face_api(payload: dict): # รีเซ็ตรับค่า payload ดูก่อน
    return {
        "success": True,
        "name": "ทดสอบผ่านระบบ Cloud Vercel"
    }

# 🎯 ปรับปรุงเพิ่ม: ดักจับคำสั่ง Preflight (OPTIONS) เคลียร์ทางให้หน้าบ้านยิงผ่านฉลุย
@app.options("/{rest_of_path:path}")
async def preflight_handler(rest_of_path: str):
    return {"message": "OK"}

# 🎯 ฟังก์ชันแถม: เอาไว้เปิดเช็กหน้าเว็บหลักเพื่อแก้บั๊ก 404
@app.get("/")
async def root():
    return {"status": "online", "backend": "Python FastAPI"}

# 🔍 ปรับแก้บรรทัดพาร์ทเริ่มต้นใน main.py (หรือ api/index.py) ของคุณ:
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # เติม dirname ครอบอีกชั้นเพื่อถอยออกจากโฟลเดอร์ api

# พาร์ทคลังรูปหมอ และไฟล์ json จะชี้ออกมาด้านนอกได้ถูกต้องแม่นยำ
DB_DOC_IMG_DIR = os.path.join(BASE_DIR, "doctor_images")
if not os.path.exists(DB_DOC_IMG_DIR):
    os.makedirs(DB_DOC_IMG_DIR)

FACE_DIR = r"D:\VScode\medical_project\backend\patient_faces"

if not os.path.exists(FACE_DIR):
    os.makedirs(FACE_DIR, exist_ok=True)

# ฟังก์ชันช่วยจัดการไฟล์ JSON
def load_json(filename: str) -> list:
    if not os.path.exists(filename): return []
    try:
        with open(filename, 'r', encoding='utf-8') as f: return json.load(f)
    except: return []

def save_json(filename: str, data: list):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# โครงสร้างสำหรับรับส่งข้อมูล
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
    image: str  # รับค่า Base64 สตริงจากกล้องหน้าเว็บ

class DoctorLoginRequest(BaseModel):
    username_or_email: str
    password: str

class AppointmentStatusUpdateRequest(BaseModel):
    apt_id: str
    status: str  
    remark: Optional[str] = ""

class StatusUpdatePayload(BaseModel):
    patient_id: str
    is_online: bool

class TelehealthMessage(BaseModel):
    patient_id: str
    sender: str
    name: str
    text: str

class PatientRegisterRequest(BaseModel):
    username: str
    name: str
    password: str
    face_image: Optional[str] = ""

GLOBAL_TELEHEALTH_DB = []
SESSION_FILE = "telehealth_session.json"


@app.get("/api/patient/dashboard/{user_id}")
async def get_dashboard(user_id: str):
    appointments = load_json("appointments.json")
    doctors = load_json("doctors.json")
    
    user_apts = [a for a in appointments if a["user_id"] == user_id]
    total_apts = len(user_apts)
    confirmed = len([a for a in user_apts if a["status"] == "CONFIRMED"])
    no_show = len([a for a in user_apts if a["status"] == "NO_SHOW"])
    
    met_doctors_dict = {}
    history = []
    
    for apt in user_apts:
        doc = next((d for d in doctors if d["doctor_id"] == apt["doctor_id"]), None)
        doc_info = doc if doc else {"name": "แพทย์ทั่วไป", "department": "ทั่วไป", "hospital": "CareSync Clinic"}
        
        history.append({
            "apt_id": apt["apt_id"],
            "date": apt["date"],
            "symptom": apt["symptom"],
            "status": apt["status"],
            "doctor_name": doc_info["name"],
            "department": doc_info["department"],
            "hospital": doc_info["hospital"],
            "cancel_remark": apt.get("cancel_remark", "")
        })
        
        if apt["status"] == "CONFIRMED" and apt["doctor_id"] not in met_doctors_dict:
            met_doctors_dict[apt["doctor_id"]] = {
                "name": doc_info["name"],
                "department": doc_info["department"],
                "hospital": doc_info["hospital"]
            }
            
    history.sort(key=lambda x: x["date"], reverse=True)
        
    return {
        "kpis": {
            "total_appointments": total_apts,
            "confirmed_visits": confirmed,
            "no_show_visits": no_show,
            "unique_doctors_met": len(met_doctors_dict)
        },
        "met_doctors": list(met_doctors_dict.values()),
        "history": history
    }


@app.post("/api/patient/ai-diagnosis")
async def ai_diagnosis(payload: AIDiagnosisRequest):
    doctors = load_json("doctors.json")
    appointments = load_json("appointments.json")
    
    if not doctors:
        raise HTTPException(status_code=500, detail="ไม่พบข้อมูลทำเนียบแพทย์ในระบบพอร์ทัล")

    if ai_client:
        try:
            doc_context = "\n".join([f"- รหัส: {d['doctor_id']}, นาม: {d['name']}, แผนก: {d['department']}, รพ.: {d['hospital']}" for d in doctors])
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
            matched_doctor = next((d for d in doctors if d["doctor_id"] == doc_id), doctors[0])
            disease = result.get("disease_tendency", "กลุ่มอาการทั่วไป")
            reason = result.get("ai_reason", "วิเคราะห์ประเมินตามพยาธิสภาพของโรค")
        except Exception as e:
            matched_doctor = random.choice(doctors)
            disease = "พบกลุ่มอาการแปรปรวน (โหมดสำรองความปลอดภัย)"
            reason = f"โครงสร้างขัดข้อง: {str(e)}"
    else:
        matched_doctor = random.choice(doctors)
        disease = "กลุ่มอาการปวดศีรษะจากความเครียด หรือออฟฟิศซินโดรมสะสม"
        reason = f"วิเคราะห์ประเมินผลอัจฉริยะจากอาการนำร่อง '{payload.symptom}'"

    future_date = (datetime.utcnow() + timedelta(days=2)).replace(hour=13, minute=0, second=0, microsecond=0)
    app_date_str = future_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    apt_id = f"apt-{len(appointments) + 1:03d}"
    new_appointment = {
        "apt_id": apt_id,
        "user_id": payload.patient_id,
        "doctor_id": matched_doctor["doctor_id"],
        "date": app_date_str,
        "symptom": payload.symptom,
        "status": "PENDING"
    }
    
    appointments.append(new_appointment)
    save_json("appointments.json", appointments)
    
    return {
        "status": "success",
        "disease_tendency": disease,
        "recommended_doctor": matched_doctor["name"],
        "department": matched_doctor["department"],
        "hospital": matched_doctor["hospital"],
        "appointment_date": app_date_str,
        "ai_reason": reason
    }


@app.post("/api/auth/login-password")
async def login_patient(payload: PatientLoginRequest):
    patients = load_json("patients.json")
    user_input = payload.username.strip()
    password_input = payload.password.strip()
    
    for p in patients:
        if p.get("username") == user_input and p.get("password") == password_input:
            return {
                "success": True,
                "user_id": p.get("user_id"),  # 🌟 บังคับคีย์นี้ส่งไป เพื่อไม่ให้หน้าบ้านได้ undefined
                "name": p.get("name")
            }
    raise HTTPException(status_code=401, detail="ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")


@app.post("/api/patient/cancel-appointment")
async def cancel_appointment_endpoint(payload: CancelAppointmentRequest):
    appointments = load_json("appointments.json")
    apt = next((a for a in appointments if a["apt_id"] == payload.apt_id), None)
    if not apt: raise HTTPException(status_code=404, detail="ไม่พบใบนัดหมาย")
        
    apt["status"] = "CANCELLED"
    apt["cancel_remark"] = payload.remark
    save_json("appointments.json", appointments)
    return {"success": True, "message": "ยกเลิกคิวตรวจสำเร็จแล้ว"}


@app.get("/api/admin/dashboard-analytics")
async def get_admin_dashboard():
    appointments = load_json("appointments.json")
    doctors = load_json("doctors.json")
    
    total_apts = len(appointments)
    confirmed = len([a for a in appointments if a.get("status") == "CONFIRMED"])
    pending = len([a for a in appointments if a.get("status") == "PENDING"])
    cancelled = len([a for a in appointments if a.get("status") == "CANCELLED"])
    no_show = len([a for a in appointments if a.get("status") == "NO_SHOW"])
    
    no_show_records = []
    for apt in appointments:
        doc = next((d for d in doctors if d.get("doctor_id") == apt.get("doctor_id")), None)
        doc_name = doc.get("name") if doc else "แพทย์ทั่วไป"
        hosp = doc.get("hospital") if doc else "CareSync Clinic"
        
        no_show_records.append({
            "patient_id": apt.get("user_id"),
            "doctor_name": doc_name,
            "hospital": hosp,
            "status": apt.get("status"), # รองรับแสดงผลทุกสถานะตามโจทย์เก่า
            "symptom": apt.get("symptom", "ไม่ระบุอาการ")
        })
            
    no_show_rate = round((no_show / total_apts) * 100, 1) if total_apts > 0 else 0
    ai_analysis = "สถิติจำนวนคิวเข้าสู่ภาวะสมดุล"
    
    if ai_client:
        try:
            sys_instruct = "คุณคือผู้อำนวยการโรงพยาบาล สรุปสถานการณ์และให้คำแนะนำเชิงบริหารสั้นๆ ไม่เกิน 2 ประโยค"
            prompt = f"สถิติคลินิกปัจจุบัน: เคสรวม={total_apts}, เข้าตรวจแล้ว={confirmed}, รอดำเนินการ={pending}, ยกเลิก={cancelled}, หลุดนัด={no_show}"
            response = ai_client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(system_instruction=sys_instruct, temperature=0.3)
            )
            ai_analysis = response.text.strip()
        except Exception as e:
            ai_analysis = f"สถิติหลุดนัดสะสม {no_show} รายการ ({str(e)})"

    return {
        "kpi_total": total_apts,
        "kpi_confirmed": confirmed,
        "kpi_pending": pending,
        "kpi_cancelled": cancelled,
        "kpi_no_show": no_show,
        "no_show_rate_percent": no_show_rate,
        "ai_analysis": ai_analysis,
        "no_show_records": no_show_records
    }


@app.post("/api/doctor/login")
async def doctor_login(payload: DoctorLoginRequest):
    doctors = load_json("doctors.json")
    user_input = payload.username_or_email.strip().lower()
    password_input = payload.password.strip()
    
    if user_input.startswith("doc-") and len(user_input) == 5:
        parts = user_input.split("-")
        if len(parts[1]) == 1: user_input = f"doc-0{parts[1]}"
            
    found_doc = None
    for doc in doctors:
        doc_id_clean = doc.get("doctor_id", "").lower()
        if (user_input == doc_id_clean) and password_input == str(doc.get("password", "1234")):
            found_doc = doc
            break
            
    if not found_doc: raise HTTPException(status_code=401, detail="ไม่พบข้อมูลสิทธิ์แพทย์")
    return {"success": True, "doctor_id": found_doc["doctor_id"], "name": found_doc["name"]}


@app.get("/api/doctor/appointments/{doctor_id}")
async def get_doctor_appointments(doctor_id: str):
    appointments = load_json("appointments.json")
    patients = load_json("patients.json")
    doc_apts = [a for a in appointments if a.get("doctor_id") == doctor_id]
    
    enriched_records = []
    for apt in doc_apts:
        patient = next((p for p in patients if p.get("user_id") == apt.get("user_id")), None)
        patient_name = patient["name"] if patient else "ผู้ป่วย CareSync User"
        user_id = apt.get("user_id")
        
        # 👤 1. ตรวจสอบชื่อไฟล์รูปจากประวัติคนไข้ 
        # ถ้าไม่มีในประวัติ ให้ตั้งชื่อไฟล์ตามรหัสผู้ป่วยไปเลย เช่น "u001.png"
        raw_face = patient.get("face_image") if patient else ""
        if not raw_face or not raw_face.endswith(('.png', '.jpg', '.jpeg')):
            raw_face = f"{user_id}.png"
            
        # 🎨 2. ตั้งค่ารูปอวาตาร์ตัวอักษรย่อเป็นแผนสำรองสุดท้าย (Fallback) ถ้าในเครื่องไม่มีรูปจริง ๆ
        encoded_name = patient_name.replace(" ", "+")
        patient_image_url = f"https://ui-avatars.com/api/?name={encoded_name}&background=0f766e&color=fff&bold=true"
        
        # 🔍 3. ตรวจสอบว่ามีไฟล์รูปนี้ (เช่น u001.png) อยู่ในโฟลเดอร์ patient_faces บนคอมพิวเตอร์จริงไหม
        # โดยแปลงรูปภาพในเครื่องคอมพิวเตอร์ให้กลายเป็น Data URL Base64 เพื่อส่งไปแสดงผลที่หน้าเว็บแผงหมอได้ทันที
        file_path = os.path.join(FACE_DIR, raw_face)
        if os.path.exists(file_path):
            try:
                with open(file_path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
                    patient_image_url = f"data:image/png;base64,{encoded_string}"
            except Exception as e:
                print(f"⚠️ ไม่สามารถเปิดอ่านไฟล์รูปในเครื่องได้ {file_path}: {e}")
        else:
            # ถ้าหาไฟล์ในเครื่องไม่เจอ ให้เช็คว่ามันเก็บสตริง Base64 เต็มตัวไว้ในไฟล์ประวัติอยู่แล้วหรือไม่
            if raw_face.startswith("data:image"):
                patient_image_url = raw_face

        enriched_records.append({
            "apt_id": apt.get("apt_id"),
            "user_id": user_id,
            "patient_name": patient_name,
            "date": apt.get("date"),
            "symptom": apt.get("symptom"),
            "status": apt.get("status"),
            "patient_image": patient_image_url  # 🚀 ส่งรูป Base64 ของไฟล์จริงในคอมพิวเตอร์ออกไปหน้าบ้าน
        })
    return {"appointments": enriched_records}


@app.post("/api/doctor/update-status")
async def doctor_update_appointment_status(payload: AppointmentStatusUpdateRequest):
    appointments = load_json("appointments.json")
    apt_index = next((i for i, a in enumerate(appointments) if a.get("apt_id") == payload.apt_id), None)
    if apt_index is None: raise HTTPException(status_code=404, detail="ไม่พบรหัสคิว")
    appointments[apt_index]["status"] = payload.status
    save_json("appointments.json", appointments)
    return {"success": True}


# 📸 ฟังก์ชันสแกนใบหน้าเข้าสู่ระบบ (เวอร์ชันส่งภาพอ้างอิงจากโฟลเดอร์ให้ AI เปรียบเทียบ)
@app.post("/api/auth/login-face")
async def login_with_face_only(payload: FaceLoginRequest):
    patients = load_json("patients.json")
    
    if not payload.image:
        raise HTTPException(status_code=400, detail="ไม่พบข้อมูลรูปภาพสแกนใบหน้า")
        
    try:
        # ล้างหัวข้อมูลสตริงรูปภาพจากเว็บแคมหน้าบ้าน
        img_data = payload.image
        if "base64," in img_data:
            img_data = img_data.split("base64,")[1]
        new_img_bytes = base64.b64decode(img_data)
    except Exception:
        raise HTTPException(status_code=400, detail="รูปแบบภาพถ่ายใบหน้าจากเว็บแคมผิดพลาด")

    if not ai_client:
        raise HTTPException(status_code=503, detail="ระบบ AI Engine ยังไม่ถูกเปิดใช้งานบนเซิร์ฟเวอร์")

    try:
        valid_patients = [p for p in patients if p.get("user_id")]
        
        # โฟลเดอร์ที่เก็บรูปภาพใบหน้าของคนไข้จริงในเครื่องคอมพิวเตอร์ของคุณ
        FACES_DIR = r"D:\VScode\medical_project\backend\patient_faces"
        
        # 📦 เตรียมรายการวัตถุ (Contents) เพื่อส่งให้ Gemini ประมวลผลร่วมกัน
        ai_contents = []
        
        # 1. แนบรูปถ่ายสดจากกล้องเว็บแคมที่ส่งเข้ามาล็อกอิน
        ai_contents.append(types.Part.from_bytes(data=new_img_bytes, mime_type='image/png'))
        
        # 2. ค้นหาและโหลดไฟล์ภาพจริงของคนไข้ทุกคนที่มีอยู่ แนบส่งไปให้ AI รู้จักโครงหน้าอ้างอิง
        patient_pool_info = []
        for p in valid_patients[:15]: # จำกัดไม่เกิน 15 คนเพื่อความเร็วสูงสุดและไม่ให้อืด
            uid = p.get("user_id")
            face_file = p.get("face_image") # เช่น "u001.png"
            
            if face_file:
                file_path = os.path.join(FACES_DIR, face_file)
                # ตรวจสอบว่ามีไฟล์รูปนี้อยู่ในโฟลเดอร์จริงหรือไม่
                if os.path.exists(file_path):
                    with open(file_path, "rb") as f:
                        saved_img_bytes = f.read()
                    
                    # แนบรูปภาพอ้างอิงของคนไข้รายนี้เข้าไปในคิวตรวจของ AI
                    ai_contents.append(types.Part.from_bytes(data=saved_img_bytes, mime_type='image/png'))
                    patient_pool_info.append(f"- รหัสผู้ป่วย: {uid}, ชื่อ: {p['name']} (ตรงกับไฟล์รูปภาพลำดับที่แนบไป)")
                else:
                    patient_pool_info.append(f"- รหัสผู้ป่วย: {uid}, ชื่อ: {p['name']} (ไม่มีไฟล์รูปอ้างอิง)")
            else:
                patient_pool_info.append(f"- รหัสผู้ป่วย: {uid}, ชื่อ: {p['name']} (ไม่มีข้อมูลรูปภาพ)")

        # 3. สร้างคำสั่ง (Prompt) อธิบายหน้างานให้ AI เข้าใจโครงสร้างภาพถ่าย
        patient_pool_text = "\n".join(patient_pool_info)
        
        sys_instruct = (
            "คุณคือระบบเปรียบเทียบอัตลักษณ์บุคคล (Face Verification System) หน้าที่ของคุณคือเปรียบเทียบรูปถ่ายใบหน้าสดรูปแรก "
            "กับรายการรูปภาพของคนไข้รายอื่น ๆ ที่แนบมาในระบบ เพื่อค้นหาว่าบุคคลในรูปสดเป็นคนไข้รหัสใด "
            "วิเคราะห์โครงสร้างใบหน้า ตา จมูก ปาก และส่งผลลัพธ์กลับมาในรูปแบบ JSON ตามโครงสร้างโครงสร้างที่กำหนดเท่านั้น"
        )
        
        prompt = (
            f"คำสั่ง: โปรดวิเคราะห์ใบหน้ารูปถ่ายสดรูปแรก ว่าตรงกับใบหน้าของคนไข้รายใดในระบบที่มีไฟล์ภาพอ้างอิงหรือไม่\n\n"
            f"รายชื่อข้อมูลระบบเวชระเบียน:\n{patient_pool_text}"
        )
        
        # ใส่ Prompt ข้อความปิดท้ายรายการเข้าไปในชุด Contents
        ai_contents.append(prompt)

        # 🚀 ส่งข้อมูลรูปสด + รูปอ้างอิงในเครื่องทั้งหมดไปให้ Gemini ประมวลผล
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=ai_contents,
            config=types.GenerateContentConfig(
                system_instruction=sys_instruct,
                response_mime_type="application/json",
                response_schema=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "is_matched": types.Schema(type=types.Type.BOOLEAN),
                        "matched_user_id": types.Schema(type=types.Type.STRING),
                        "confidence_percent": types.Schema(type=types.Type.INTEGER)
                    },
                    required=["is_matched", "matched_user_id"]
                ),
                temperature=0.1
            )
        )
        
        result = json.loads(response.text.strip())
        print(f"🔮 AI วิเคราะห์ผลสำเร็จ: {result}")
        
        # ค้นหาค่าและตรวจสอบเกณฑ์แมตช์อัตลักษณ์ (มั่นใจเกิน 80% ขึ้นไป)
        if result.get("is_matched") and result.get("confidence_percent", 0) >= 80:
            target_uid = result.get("matched_user_id")
            matched_patient = next(
                (p for p in valid_patients if str(p.get("user_id", "")) == str(target_uid)), 
                None
            )
            if matched_patient:
                return {
                    "success": True, 
                    "user_id": matched_patient["user_id"], 
                    "name": matched_patient["name"]
                }

    except Exception as e:
        print(f"🚨 [Face Login Error Log]: {str(e)}")
        if "getaddrinfo failed" in str(e) or "Cannot connect to host" in str(e):
            raise HTTPException(status_code=503, detail="⚠️ เครื่องเซิร์ฟเวอร์ไม่สามารถเชื่อมต่อระบบเครือข่ายภายนอกได้")
        raise HTTPException(status_code=500, detail="เกิดข้อผิดพลาดภายในการประมวลผลเซิร์ฟเวอร์")

    raise HTTPException(status_code=401, detail="โครงสร้างอัตลักษณ์ใบหน้าปัจจุบันไม่ตรงกับผู้ป่วยรายใดในระบบ")


def load_sessions() -> list:
    if not os.path.exists(SESSION_FILE): return []
    try:
        with open(SESSION_FILE, "r", encoding="utf-8") as f: return json.load(f)
    except: return []

def save_sessions(sessions: list):
    with open(SESSION_FILE, "w", encoding="utf-8") as f: json.dump(sessions, f, indent=4, ensure_ascii=False)

@app.post("/api/telehealth/update-status")
async def update_telehealth_status(payload: StatusUpdatePayload):
    sessions = load_sessions()
    updated = False
    for s in sessions:
        if s["patient_id"] == payload.patient_id:
            s["is_online"] = payload.is_online
            updated = True
            break
    if not updated:
        sessions.append({"patient_id": payload.patient_id, "patient_name": f"ผู้ป่วยรหัส {payload.patient_id}", "is_online": payload.is_online})
    save_sessions(sessions)
    return {"success": True}

@app.post("/api/telehealth/send")
async def send_telehealth_message(msg: TelehealthMessage):
    GLOBAL_TELEHEALTH_DB.append(msg.dict())
    return {"success": True}

@app.get("/api/telehealth/history")
async def get_telehealth_history(patient_id: str):
    return [c for c in GLOBAL_TELEHEALTH_DB if c["patient_id"] == patient_id]

@app.get("/api/telehealth/patients")
async def get_active_chat_patients():
    sessions = load_sessions()
    sessions.sort(key=lambda x: (-1 if x.get("is_online") else 0, x.get("patient_id", "")))
    return sessions

@app.get("/api/doctor/appointments/{doctor_id}")
async def get_doctor_appointments(doctor_id: str):
    appointments = load_json("appointments.json")
    patients = load_json("patients.json")
    doc_apts = [a for a in appointments if a.get("doctor_id") == doctor_id]
    
    enriched_records = []
    for apt in doc_apts:
        patient = next((p for p in patients if p.get("user_id") == apt.get("user_id")), None)
        patient_name = patient["name"] if patient else "ผู้ป่วย CareSync User"
        
        # 👤 1. ดึงข้อมูลรูปภาพใบหน้าคนไข้
        raw_face = patient.get("face_image") if patient else ""
        
        # 🎨 2. สร้างภาพอวาตาร์สำรองทันที (Fallback UI-Avatar ตามชื่อคนไข้) 
        # เพื่อป้องกันปัญหาหน้าจอแตกกรณีค่ารูปเป็นค่าว่าง หรือส่งค่าผิดพลาด
        encoded_name = patient_name.replace(" ", "+")
        patient_image_url = f"https://ui-avatars.com/api/?name={encoded_name}&background=0f766e&color=fff&bold=true"
        
        # ตรวจสอบรูปแบบข้อมูลรูปภาพในฐานข้อมูล
        if raw_face and (raw_face.startswith("data:image") or len(raw_face) > 100):
            patient_image_url = raw_face
        elif raw_face and raw_face.endswith(('.png', '.jpg', '.jpeg')):
            patient_image_url = f"/patient_faces/{raw_face}"
        elif raw_face and raw_face.startswith("http"):
            patient_image_url = raw_face

        enriched_records.append({
            "apt_id": apt.get("apt_id"),
            "user_id": apt.get("user_id"),
            "patient_name": patient_name,
            "date": apt.get("date"),
            "symptom": apt.get("symptom"),
            "status": apt.get("status"),
            "patient_image": patient_image_url  # 🚀 การันตีว่าส่งค่า String URL ที่ใช้งานได้จริงเสมอ
        })
    return {"appointments": enriched_records}

# -----------------------------------------------------------------
# 🚀 อัปเดตร่วมกับ Endpoint สมัครสมาชิกเดิมของคุณ (ตัวอย่างโครงสร้างไอดีใหม่)
# -----------------------------------------------------------------
# สมมติว่าในฟังก์ชัน @app.post("/api/patient/register") เดิมของคุณทำงานเสร็จสิ้น
# ให้แทรกคำสั่งเรียกฟังก์ชัน register_new_patient_to_telehealth ด้านบนเข้าไป เช่น:
#
# @app.post("/api/patient/register")
# async def register_patient(payload: dict):
#     ... โค้ดสมัครสมาชิกเดิมของคุณ ...
#     new_id = f"u{len(total_patients):03d}" # หรือ u002, u003 ตามกลไกเดิมของคุณ
#     
#     # สั่งซิงค์เข้าคลังแชททันทีที่มีการสมัครใหม่สำเร็จ:
#     register_new_patient_to_telehealth(new_id, payload.get("name"))
#     return {"success": True, "patient_id": new_id}


# -----------------------------------------------------------------
# API เส้นทางรับส่งและจัดเรียงข้อมูลตามเงื่อนไข (ดัน Online ขึ้นก่อน -> เรียงตามรหัสคิวน้อยไปมาก)
# -----------------------------------------------------------------

@app.post("/api/telehealth/send")
async def send_telehealth_message(msg: TelehealthMessage):
    GLOBAL_TELEHEALTH_DB.append(msg.dict())
    return {"success": True}

@app.get("/api/telehealth/history")
async def get_telehealth_history(patient_id: str):
    return [c for c in GLOBAL_TELEHEALTH_DB if c["patient_id"] == patient_id]

@app.get("/api/telehealth/patients")
async def get_active_chat_patients():
    """ 
    ดึงรายชื่อคนไข้ทั้งหมด (รวมถึงผู้ใช้งานที่เพิ่งสมัครเข้ามาใหม่)
    - ใครออนไลน์ (is_online == True) จะถูกจัดไว้บนสุด
    - คนที่สมัครใหม่ / ออฟไลน์ (is_online == False) จะถูกจัดเรียงตามรหัสไอดีจากน้อยไปมากต่อท้ายลงมา
    """
    sessions = load_sessions()
    
    # เรียงลำดับ: ออนไลน์สแตนด์บายขึ้นก่อน (-1 คือ True, 0 คือ False) -> ตามด้วยอักษรรหัสคนไข้ (u001, u002, u003) จากน้อยไปมาก
    sessions.sort(key=lambda x: (-1 if x.get("is_online") else 0, x.get("patient_id", "")))
    
    return sessions

class FaceLoginRequest(BaseModel):
    username: str   # <--- คาดหวังคำว่า username หรือ user_id?
    image: str      # <--- คาดหวังข้อมูล Base64 ของรูปภาพ

# 👤 1. API เส้นทางรับลงทะเบียนข้อมูลคนไข้ใหม่ (แก้ไขปัญหา 404 Not Found)
@app.post("/api/patient/register")
async def register_patient(payload: PatientRegisterRequest):
    try:
        # โหลดข้อมูลคนไข้เดิมที่มีอยู่ในระบบมาเตรียมไว้
        patients = load_json("patients.json")
    except Exception:
        patients = []

    # 1. เช็กตรวจสอบว่า Username ซ้ำกับคนในระบบแล้วหรือไม่
    if any(p.get("username") == payload.username for p in patients):
        raise HTTPException(status_code=400, detail="ชื่อผู้ใช้งาน (Username) นี้ถูกใช้ไปแล้วในระบบ")

    # 2. ทำการ Generate รหัสผู้ป่วยใหม่แบบอัตโนมัติ (เช่น u001, u002, u003...)
    next_num = 1
    if patients:
        # ค้นหาค่าตัวเลขที่มากที่สุดจากไอดีเดิมที่มีอยู่
        existing_ids = []
        for p in patients:
            uid_str = p.get("user_id", "u000")
            if uid_str.startswith("u"):
                try:
                    existing_ids.append(int(uid_str[1:]))
                except ValueError:
                    pass
        if existing_ids:
            next_num = max(existing_ids) + 1
            
    new_user_id = f"u{next_num:03d}"  # ผลลัพธ์จะได้โครงสร้าง u012 เป็นต้น
    new_filename = f"{new_user_id}.png"

    # 3. ตรวจสอบการส่งรูปภาพลงทะเบียนแบบ Base64 (แก้ไข Path ให้ลงโฟลเดอร์ patient_faces)
    if payload.face_image and "base64," in payload.face_image:
        try:
            img_data = payload.face_image.split("base64,")[1]
            img_bytes = base64.b64decode(img_data)
            
            # 🎯 ปรับปรุง Path เป็นโฟลเดอร์ปลายทางตามที่คุณเจาะจง
            target_dir = r"D:\VScode\medical_project\backend\patient_faces"
            
            # ตรวจสอบและสร้างโฟลเดอร์อัตโนมัติหากยังไม่มีในเครื่อง
            if not os.path.exists(target_dir):
                os.makedirs(target_dir, exist_ok=True)
                
            # ใช้ os.path.join เพื่อประกอบ Path ให้เป็นมาตรฐานสากลและเสถียรที่สุดบน Windows
            final_file_path = os.path.join(target_dir, new_filename)
            
            with open(final_file_path, "wb") as f:
                f.write(img_bytes)
                
            print(f"📸 [Success] บันทึกไฟล์ภาพถ่ายใบหน้าสำเร็จที่: {final_file_path}")
            
        except Exception as e:
            print(f"🚨 [Register Image Write Error]: บันทึกไฟล์ภาพล้มเหลวเนื่องจาก -> {e}")

    # 4. ประกอบโครงสร้างข้อมูลเพื่อบันทึกลงไฟล์ JSON
    new_patient_data = {
        "user_id": new_user_id,
        "username": payload.username,
        "name": payload.name,
        "password": payload.password,
        "face_image": new_filename if payload.face_image else ""
    }
    
    patients.append(new_patient_data)
    
    # บันทึกข้อมูลทั้งหมดกลับลงไปที่ไฟล์ JSON หลัก
    try:
        with open("patients.json", "w", encoding="utf-8") as f:
            json.dump(patients, f, indent=4, ensure_ascii=False)
    except Exception:
        raise HTTPException(status_code=500, detail="ไม่สามารถเขียนข้อมูลลงฐานข้อมูลระบบได้")

    # 5. ลงทะเบียนเซสชันแชต Telehealth สำรองไว้ให้คนไข้ใหม่ทันที (ตามคอมเมนต์ในโค้ดเดิมของคุณ)
    try:
        sessions = load_json("telehealth_session.json")
    except Exception:
        sessions = []
        
    sessions.append({
        "patient_id": new_user_id,
        "patient_name": payload.name,
        "is_online": False
    })
    
    try:
        with open("telehealth_session.json", "w", encoding="utf-8") as f:
            json.dump(sessions, f, indent=4, ensure_ascii=False)
    except Exception:
        pass

    # ส่งผลลัพธ์กลับไปแจ้งฝั่งหน้าบ้าน
    return {
        "success": True, 
        "user_id": new_user_id, 
        "name": payload.name
    }

# 🛠️ 1. เพิ่ม Endpoint เพื่อส่งข้อมูลรายชื่อแพทย์จากไฟล์ doctors.json จริงออกไป
@app.get("/api/doctors")
async def get_all_doctors():
    json_path = r"D:\VScode\medical_project\backend\doctors.json"
    
    if not os.path.exists(json_path):
        raise HTTPException(status_code=404, detail="ไม่พบไฟล์คลังข้อมูล doctors.json ในระบบคอมพิวเตอร์ของคุณ")
        
    try:
        with open(json_path, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"การอ่านไฟล์ข้อมูลขัดข้อง: {str(e)}")

# 🛠️ 2. เมาท์เปิดพอร์ตรูปภาพ Static เพื่อส่งภาพ doc-1.png, doc-2.png ไปแสดงบนหน้าเว็บหลัก
# หมายเหตุ: หากโค้ดหลักของคุณเคย Mount ไปที่อื่นแล้ว ให้ตรวจเช็กชื่อโฟลเดอร์ให้ตรงกัน
img_dir = r"D:\VScode\medical_project\backend\doctor_images"
if os.path.exists(img_dir):
    app.mount("/doctor_images", StaticFiles(directory=img_dir), name="doctor_images")
