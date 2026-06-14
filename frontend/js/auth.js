/**
 * CareSync Patient Portal - Authentication System
 * รองรับการล็อกอินด้วยรหัสผ่านปกติ และระบบ Face Login (Gemini AI Validation)
 */

let currentMode = 'login';
let base64ImageString = null;

// ดึง Elements ที่ต้องใช้งานร่วมกันจากหน้าเว็บ (auth.html)
const video = document.getElementById('webcam');
const canvas = document.getElementById('capturedCanvas');
const placeholder = document.getElementById('camPlaceholder');
const captureBtn = document.getElementById('btnCapture');

// 🎯 ฟังก์ชันเสกตัวหมุนให้ลอยครอบตำแหน่งของ "กล้อง" พอดีเป๊ะ (ไม่ต้องยุ่งกับ HTML)
function toggleCamSpinner(show, message = "กำลังประมวลผล...") {
    let spinnerBox = document.getElementById('camDynamicSpinner');
    
    if (show) {
        // หา Element หลักที่เป็นตัวคลุมกล้อง (หาพื้นที่อ้างอิงเพื่อแปะ Spinner ลงไป)
        const targetContainer = video ? video.parentElement : null;
        if (!targetContainer) return;

        // บังคับให้ Parent ของกล้องรองรับการซ้อนวัตถุแบบ Relative
        targetContainer.style.position = 'relative';

        if (!spinnerBox) {
            spinnerBox = document.createElement('div');
            spinnerBox.id = 'camDynamicSpinner';
            // แต่งสไตล์ด้วย Tailwind CSS ให้ลอยอยู่บนตัวเฟรมกล้องแบบ Smooth
            spinnerBox.className = 'absolute inset-0 bg-slate-900/70 backdrop-blur-xs flex flex-col items-center justify-center text-white font-medium z-40 rounded-2xl gap-3 transition-all duration-300';
            spinnerBox.innerHTML = `
                <div class="relative flex items-center justify-center">
                    <div class="w-10 h-10 border-4 border-teal-500 border-t-transparent rounded-full animate-spin"></div>
                    <span class="absolute text-xs">📸</span>
                </div>
                <p id="camSpinnerMsg" class="text-xs bg-slate-800/90 text-teal-300 px-3 py-1.5 rounded-lg border border-slate-700 shadow-md tracking-wide animate-pulse">${message}</p>
            `;
            targetContainer.appendChild(spinnerBox);
        } else {
            document.getElementById('camSpinnerMsg').innerText = message;
            spinnerBox.classList.remove('hidden', 'opacity-0');
        }
    } else {
        if (spinnerBox) {
            spinnerBox.classList.add('hidden');
        }
    }
}

// 🔹 ฟังก์ชันสลับแท็บระหว่าง เข้าสู่ระบบ และ สมัครสมาชิก
function switchTab(mode) {
    currentMode = mode;
    stopWebcam();
    toggleCamSpinner(false);
    
    // จัดการแสดงผลฟอร์ม
    document.getElementById('loginForm').classList.toggle('hidden', mode !== 'login');
    document.getElementById('registerForm').classList.toggle('hidden', mode !== 'register');
    
    // จัดการสไตล์ของปุ่มแท็บ
    document.getElementById('tabLogin').className = mode === 'login' 
        ? 'flex-1 pb-3 font-bold text-teal-600 border-b-2 border-teal-600' 
        : 'flex-1 pb-3 font-medium text-slate-400';
    document.getElementById('tabRegister').className = mode === 'register' 
        ? 'flex-1 pb-3 font-bold text-teal-600 border-b-2 border-teal-600' 
        : 'flex-1 pb-3 font-medium text-slate-400';
}

// 🔹 ฟังก์ชันเปิดใช้งานกล้องเว็บแคม
async function startWebcam() {
    if (placeholder) placeholder.classList.add('hidden');
    if (video) video.classList.remove('hidden');
    if (canvas) canvas.classList.add('hidden');
    if (captureBtn) captureBtn.classList.remove('hidden');
    base64ImageString = null;
    toggleCamSpinner(false);

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
            video: { 
                width: { ideal: 400 }, 
                height: { ideal: 300 },
                facingMode: "user" 
            } 
        });
        video.srcObject = stream;
    } catch (err) {
        alert("ไม่สามารถเข้าถึงกล้องถ่ายรูปได้: " + err);
        stopWebcam();
    }
}

// 🔹 ฟังก์ชันปิดการใช้งานกล้อง
function stopWebcam() {
    if (video && video.srcObject) {
        video.srcObject.getTracks().forEach(track => track.stop());
    }
    if (video) video.classList.add('hidden');
    if (canvas) canvas.classList.add('hidden');
    if (captureBtn) captureBtn.classList.add('hidden');
    if (placeholder) placeholder.classList.remove('hidden');
    toggleCamSpinner(false);
}

// 📸 ฟังก์ชันจับภาพนิ่งจากสัญญาณวิดีโอ (Snapshot)
function captureSnapshot() {
    if (!video) return;
    
    // 🎯 สั่งแสดงวงกลมหมุนอนิเมชันคร่อมทับบนกล้องทันทีที่กด "📸 กดบันทึกภาพถ่ายใบหน้ามุมตรง"
    toggleCamSpinner(true, "⚡ กำลังบันทึกพิกัดใบหน้า...");

    // หน่วงเวลา 60ms เพื่อยอมให้ UI วาดสปินเนอร์ขึ้นมาก่อนที่จะประมวลผลบิตแมปภาพขนาดใหญ่
    setTimeout(() => {
        try {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            
            base64ImageString = canvas.toDataURL('image/png');
            
            // แสดงรูปภาพที่บันทึกแล้วนิ่งไว้บนหน้าจอเพื่อความสวยงาม
            video.classList.add('hidden');
            canvas.classList.remove('hidden');
            captureBtn.classList.add('hidden');

            if (currentMode === 'login') {
                // เปลี่ยนข้อความเป็นสถานะยิงปัญญาประดิษฐ์สแกนจับคู่ระเบียนคนไข้
                toggleCamSpinner(true, "🔮 AI กำลังวิเคราะห์อัตลักษณ์ใบหน้า...");
                processFaceLogin();
            } else {
                // โหมดสมัครสมาชิก: ทำการซ่อนสปินเนอร์เพื่อให้คนไข้เห็นใบหน้าตัวเอง และกรอกฟอร์มต่อ
                toggleCamSpinner(false);
                alert("บันทึกพิกัดใบหน้าเรียบร้อย! กรุณากรอกฟอร์มต่อให้ครบถ้วนแล้วกดลงทะเบียน");
                if (video.srcObject) video.srcObject.getTracks().forEach(track => track.stop());
            }
        } catch (err) {
            toggleCamSpinner(false);
            console.error("Capture Error:", err);
            alert("เกิดข้อผิดพลาดระหว่างบันทึกรูปภาพ");
        }
    }, 60);
}

// 🔹 API: ยื่นขอลงทะเบียนสมัครสมาชิกคนไข้ใหม่
async function submitRegister() {
    const username = document.getElementById('regUser').value.trim();
    const name = document.getElementById('regName').value.trim();
    const password = document.getElementById('regPass').value.trim();

    if (!username || !name || !password) {
        return alert("กรุณากรอกข้อมูลส่วนตัวคนไข้ให้ครบถ้วน");
    }
    
    const payload = {
        username: username,
        name: name,
        password: password,
        face_image: base64ImageString || ""
    };

    try {
        toggleCamSpinner(true, "👤 กำลังบันทึกเวชระเบียน...");
        const res = await fetch('/api/patient/register', { 
            method: 'POST', 
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const data = await res.json();
        toggleCamSpinner(false);

        if (res.ok) {
            alert("สมัครสมาชิกสำเร็จ! รหัสผู้ป่วยของคุณคือ: " + (data.user_id || data.patient_id));
            switchTab('login');
        } else { 
            alert(data.detail || "ลงทะเบียนไม่สำเร็จ"); 
        }
    } catch (err) { 
        toggleCamSpinner(false);
        alert("เกิดข้อผิดพลาดในการเชื่อมต่อเซิร์ฟเวอร์ลงทะเบียน"); 
    }
}

// ⌨️ ฟังก์ชันเข้าสู่ระบบด้วยรหัสผ่านปกติ (Password Login)
async function submitPasswordLogin() {
    const username = document.getElementById('loginUser').value.trim();
    const password = document.getElementById('loginPass').value.trim();

    if (!username || !password) {
        alert("⚠️ กรุณากรอกทั้ง Username และรหัสผ่านเพื่อเข้าใช้งาน");
        return;
    }

    try {
        toggleCamSpinner(true, "🔑 กำลังยืนยันรหัสผ่าน...");
        const response = await fetch('/api/auth/login-password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username: username, password: password })
        });

        const data = await response.json();
        toggleCamSpinner(false);

        if (response.ok && data.success) {
            localStorage.setItem("care_user_id", data.user_id);
            localStorage.setItem("care_user_name", data.name);
            window.location.href = "dashboard.html";
        } else {
            alert(`❌ ข้อมูลไม่ถูกต้อง: ${data.detail || "ชื่อผู้ใช้หรือรหัสผ่านผิดพลาด"}`);
        }
    } catch (error) {
        toggleCamSpinner(false);
        console.error("Password Login Error:", error);
        alert("🚨 ระบบล็อกอินผ่านรหัสผ่านขัดข้อง");
    }
}

// 🔹 ฟังก์ชันเรียกประมวลผลระบบสแกนใบหน้า
function submitFaceLogin() {
    processFaceLogin();
}

// 🔹 API: ล็อกอินด้วยระบบสแกนใบหน้า (Face Login Engine)
async function processFaceLogin() {
    if (!base64ImageString) {
        alert("🚨 ไม่พบข้อมูลภาพถ่ายใบหน้า กรุณาเปิดกล้องสแกนใหม่อีกครั้ง");
        toggleCamSpinner(false);
        return;
    }

    const payload = {
        username: "face_mode",
        image: base64ImageString
    };

    try {
        // รักษาเอฟเฟกต์ตัวหมุนและปรับข้อความให้ชัดเจน
        toggleCamSpinner(true, "🔮 AI กำลังวิเคราะห์อัตลักษณ์ใบหน้า...");

        const response = await fetch('/api/auth/login-face', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        
        // 🛑 เคลียร์ซ่อนตัวหมุนออกจากเฟร้มกล้องทันทีที่ได้รับข้อมูลส่งกลับจาก Backend
        toggleCamSpinner(false);

        if (response.ok && data.success) {
            alert(`🎉 สแกนใบหน้าสำเร็จ! ยินดีต้อนรับคุณ: ${data.name}`);
            
            localStorage.setItem("care_user_id", data.user_id);
            localStorage.setItem("care_user_name", data.name);
            window.location.href = "dashboard.html";
        } else {
            alert(`⚠️ สแกนใบหน้าไม่ผ่าน: ${data.detail || 'โครงหน้าไม่ตรงกับฐานข้อมูล'}`);
            startWebcam();
        }
    } catch (error) {
        toggleCamSpinner(false);
        console.error("Face Auth Exception:", error);
        alert("🚨 ระบบเชื่อมต่อฐานข้อมูลภาพถ่ายขัดข้อง");
        startWebcam();
    }
}
