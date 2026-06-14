from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# สั่งปลดล็อกประตูหน้าบ้าน CORS ในระดับโค้ด Python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FaceLoginPayload(BaseModel):
    username: str
    image: str

# พาร์ทหลักสำหรับรับภาพสแกนใบหน้า
@app.post("/api/auth/login-face")
async def login_face_api(payload: FaceLoginPayload):
    return {
        "success": True,
        "name": "ยินดีต้อนรับ! ระบบหลังบ้าน Python ทำงานสำเร็จแล้ว"
    }

# ดักจับ Preflight (OPTIONS) เผื่อกรณีเบราว์เซอร์วิ่งทะลุกำแพงเซิร์ฟเวอร์เข้ามา
@app.options("/api/auth/login-face")
async def options_handler():
    return {"message": "OK"}

# พาร์ทหน้าแรกสำหรับเอาไว้คลิกเช็กสถานะระบบ
@app.get("/api")
async def root_check():
    return {"status": "online", "message": "FastAPI is running on Vercel!"}

# 🎯 เพิ่มโค้ดชุดนี้เข้าไปท้ายไฟล์ api/index.py เพื่อดักจับหน้าแรกสุด
@app.get("/")
async def read_root():
    return {
        "status": "online",
        "system": "HAMOR MEDICAL API Server Gateway",
        "docs": "/api"
    }