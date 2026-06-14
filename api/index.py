from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

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

@app.post("/api/auth/login-face")
async def login_face_api(payload: FaceLoginPayload):
    try:
        username = payload.username
        image_base64 = payload.image

        # 🛑 เช็กดักบั๊ก: ถ้าหน้าบ้านส่งข้อมูลมาไม่ครบ ห้ามให้ผ่าน
        if not username or not image_base64 or "data:image" not in image_base64:
            return {
                "success": False,
                "detail": "ไม่พบข้อมูลชื่อผู้ใช้ หรือภาพถ่ายใบหน้าผิดพลาด"
            }

        # -------------------------------------------------------------
        # 🎯 [จุดใส่โค้ด Gemini AI ของคุณ]
        # ตัวอย่าง: ค่าเริ่มต้นให้ตรวจสอบผ่าน (คุณเอาฟังก์ชันตรวจจริงมาใส่ตรงนี้ได้เลย)
        is_authenticated = True 
        # -------------------------------------------------------------

        if is_authenticated:
            return {
                "success": True,
                "name": username,
                "user_id": f"PT-{username.upper()}" # ดึงไอดีไปใช้ในหน้าแดชบอร์ดต่อ
            }
        else:
            return {
                "success": False,
                "detail": "สแกนใบหน้าไม่ผ่าน อัตลักษณ์ไม่ตรงกับระบบ"
            }

    except Exception as e:
        return {"success": False, "detail": str(e)}

@app.options("/api/auth/login-face")
async def options_handler():
    return {"message": "OK"}

@app.get("/api")
async def health_check():
    return {"status": "online", "backend": "FastAPI on Vercel Python 3.12"}