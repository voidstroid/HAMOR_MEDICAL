from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 🎯 บังคับตั้งชื่อว่า app เท่านั้น ห้ามเปลี่ยน!
app = FastAPI() 

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api")
async def check_online():
    return {"status": "online"}