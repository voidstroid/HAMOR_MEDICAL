/**
 * ==================================================================
 * 🏥 CARESYNC PORTAL - CLEAN ENGINE (STABLE REALTIME VERSION)
 * ==================================================================
 */

const API_BASE_URL = '/api/patient';
const userId = localStorage.getItem('care_user_id');
const userName = localStorage.getItem('care_user_name');
let fullHistoryData = []; // State ข้อมูลกลางประจำหน้าแอป SPA

if (!userId) { 
    window.location.href = 'auth.html'; 
}

/**
 * 📊 รีเฟรชและป้อนข้อมูลเชิงสถิติกราฟิกเฉพาะจุดลงบนแผงควบคุม
 */
async function fetchDashboardData() {
    try {
        const res = await fetch(`${API_BASE_URL}/dashboard/${userId}`);
        if (!res.ok) throw new Error("ไม่สามารถเชื่อมต่อฐานข้อมูลหลักได้");
        const data = await res.json();

        // เขียนการ์ด KPIs
        document.getElementById('kpiTotal').innerText = (data.kpis.total_appointments || 0) + ' ครั้ง';
        document.getElementById('kpiMet').innerText = (data.kpis.confirmed_visits || 0) + ' ครั้ง';
        document.getElementById('kpiNoShow').innerText = (data.kpis.no_show_visits || 0) + ' ครั้ง';
        document.getElementById('kpiDoc').innerText = (data.kpis.unique_doctors_met || 0) + ' ท่าน';

        // วาดทำเนียบรายชื่อแพทย์คุณหมอที่เคยพบเจอแล้ว
        const docContainer = document.getElementById('doctorsMetContainer');
        if (docContainer) {
            docContainer.innerHTML = '';
            if (!data.met_doctors || data.met_doctors.length === 0) {
                docContainer.innerHTML = `<div class="text-slate-400 text-xs py-2">🩺 ยังไม่มีประวัติการพบแพทย์เฉพาะทางสำเร็จ</div>`;
            } else {
                data.met_doctors.forEach(d => {
                    docContainer.innerHTML += `
                        <div class="p-3 bg-slate-50 rounded-xl border border-slate-100 text-xs shadow-2xs">
                            <p class="font-bold text-slate-900">👨‍⚕️ ${d.name}</p>
                            <p class="text-[10px] text-slate-500 mt-0.5">แผนก${d.department} • ${d.hospital}</p>
                        </div>`;
                });
            }
        }

        // จัดการตารางนัดหมาย
        fullHistoryData = data.history || [];
        renderHistoryTable(fullHistoryData);

    } catch (err) { 
        console.error("CareSync Engine Error:", err); 
    }
}

/**
 * 📋 เรนเดอร์อัปเดตแถวตารางแบบเรียลไทม์
 */
function renderHistoryTable(list) {
    const tbody = document.getElementById('historyTableBody');
    if (!tbody) return;
    
    if (list.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="p-4 text-center text-slate-400">🔍 ไม่พบรายการนัดหมายในฐานข้อมูลของคุณ</td></tr>`;
        return;
    }
    
    tbody.innerHTML = '';
    list.forEach(item => {
        let statusBadge = "bg-slate-100 text-slate-600";
        let actionElement = `<span class="text-slate-400 text-xs">-</span>`;

        if (item.status === "CONFIRMED") {
            statusBadge = "bg-emerald-50 text-emerald-600 font-bold border border-emerald-200";
            actionElement = `<span class="text-emerald-500 text-xs font-semibold">เข้าตรวจแล้ว</span>`;
        }
        else if (item.status === "PENDING") {
            statusBadge = "bg-amber-50 text-amber-600 font-bold border border-amber-200";
            actionElement = `<button onclick="cancelAppointment(event, '${item.apt_id}')" class="px-2.5 py-1 bg-rose-500 hover:bg-rose-600 text-white rounded-lg text-[11px] transition-colors font-medium">ยกเลิกคิว</button>`;
        }
        else if (item.status === "CANCELLED") {
            statusBadge = "bg-slate-100 text-slate-400 border border-slate-200";
            actionElement = item.cancel_remark 
                ? `<span class="text-slate-400 text-[10px] block max-w-[140px] truncate" title="${item.cancel_remark}">เหตุผล: ${item.cancel_remark}</span>` 
                : `<span class="text-slate-400 text-xs">ยกเลิกคิวแล้ว</span>`;
        }
        else if (item.status === "NO_SHOW") {
            statusBadge = "bg-rose-50 text-rose-600 font-bold border border-rose-100";
            actionElement = `<span class="text-rose-400 text-xs">ขาดการติดต่อ</span>`;
        }

        tbody.innerHTML += `
            <tr class="hover:bg-slate-50/80 transition text-[11px] sm:text-xs">
                <td class="p-4 font-mono font-medium text-slate-400">${item.apt_id}</td>
                <td class="p-4 font-medium">${new Date(item.date).toLocaleString('th-TH')}</td>
                <td class="p-4 font-bold text-slate-900">${item.doctor_name}<br><span class="text-[10px] text-slate-400 font-normal">${item.hospital} • แผนก${item.department}</span></td>
                <td class="p-4 text-slate-500 max-w-xs truncate" title="${item.symptom}">${item.symptom}</td>
                <td class="p-4 flex items-center justify-between gap-2 mt-1">
                    <span class="px-2 py-0.5 rounded text-[10px] ${statusBadge}">${item.status}</span>
                    <div class="text-right pr-2">${actionElement}</div>
                </td>
            </tr>`;
    });
}

/**
 * 🤖 ส่งฟอร์มให้ AI วิเคราะห์โรคแบบสดข้ามโครงข่ายโดเมน
 */
async function diagnoseDisease(event) {
    if (event) event.preventDefault(); // 🛑 ดักจับหยุดพฤติกรรมดั้งเดิมไม่ให้เว็บโหลดใหม่

    const symptomInput = document.getElementById('symptomInput');
    const symptom = symptomInput.value.trim();
    if (!symptom) return alert("กรุณากรอกระบุอาการเจ็บป่วยก่อนส่งให้ปัญญาประดิษฐ์ประมวลผล");

    const resultCard = document.getElementById('diagResultCard');
    if (resultCard) resultCard.classList.remove('hidden');
    
    document.getElementById('resDisease').innerText = "🔄 กำลังเรียกใช้โมเดล Gemini AI...";
    document.getElementById('resReason').innerText = "ระบบคอมพิวเตอร์กำลังประเมินโรคและคำนวณจับคู่สล็อตเวลาตารางรักษาของคุณหมอผู้เชี่ยวชาญ...";

    try {
        const res = await fetch(`${API_BASE_URL}/ai-diagnosis`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ patient_id: userId, symptom: symptom })
        });
        const data = await res.json();

        if (res.ok) {
            // เขียนทับค่าหน้าจอ ค้างไว้ถาวรอย่างปลอดภัย
            document.getElementById('resDisease').innerText = `โรคที่เป็นไปได้: ${data.disease_tendency}`;
            document.getElementById('resReason').innerText = data.ai_reason;
            document.getElementById('resDocName').innerText = data.recommended_doctor;
            document.getElementById('resDept').innerText = data.department;
            document.getElementById('resHosp').innerText = data.hospital;
            document.getElementById('resDate').innerText = new Date(data.appointment_date).toLocaleString('th-TH') + " น.";

            symptomInput.value = ""; // เคลียร์ช่องพิมพ์
            fetchDashboardData();   // ดึงประวัตินัดหมายใหม่มาต่อท้ายตารางแบบเงียบๆ
        } else {
            alert(`⚠️ ข้อผิดพลาด: ${data.detail}`);
        }
    } catch (err) { 
        alert("🚨 ระบบตรวจพบปัญหาความปลอดภัยในการเชื่อมต่อข้าม Origin โดเมนหลังบ้าน"); 
    }
}

/**
 * ❌ ฟังก์ชันส่งยกเลิกคิวนัดหมาย
 */
async function cancelAppointment(event, aptId) {
    if (event) event.preventDefault();

    const remark = prompt(`คุณแน่ใจหรือไม่ว่าต้องการยกเลิกใบนัดหมายคิวตรวจสุขภาพรหัส: ${aptId} ?\n\nระบุหมายเหตุความจำเป็น:`);
    if (remark === null) return; 

    try {
        const response = await fetch(`${API_BASE_URL}/cancel-appointment`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ apt_id: aptId, remark: remark.trim() })
        });

        if (response.ok) {
            alert("✅ บันทึกคำขอยกเลิกใบนัดตรวจเรียบร้อยแล้ว");
            fetchDashboardData(); 
        } else {
            const err = await response.json();
            alert(`⚠️ ล้มเหลว: ${err.detail}`);
        }
    } catch (error) {
        alert("🚨 การติดต่อขอยกเลิกกับเซิร์ฟเวอร์เกิดข้อขัดข้อง");
    }
}

/**
 * ⚡ Live Search ค้นหาข้อมูลตารางเรียลไทม์
 */
function applyFilterAndSearch() {
    const searchTerm = document.getElementById('tableSearch').value.toLowerCase().trim();
    const statusFilter = document.getElementById('statusFilter').value;

    const filteredResult = fullHistoryData.filter(item => {
        const matchSearch = item.doctor_name.toLowerCase().includes(searchTerm) || item.symptom.toLowerCase().includes(searchTerm);
        const matchStatus = statusFilter === 'ALL' || item.status === statusFilter;
        return matchSearch && matchStatus;
    });
    renderHistoryTable(filteredResult);
}

function logout() {
    localStorage.clear();
    window.location.href = 'auth.html';
}

document.addEventListener("DOMContentLoaded", () => {
    // ดึงค่าชื่อแพทย์ และใส่ข้อความสำรองหากค่าเป็น Null/Undefined
    const doctorName = localStorage.getItem("doc_name") || "แพทย์เวรประจำศูนย์";
    
    const welcomeElem = document.getElementById("welcomeDocName");
    if (welcomeElem) {
        welcomeElem.innerText = `👨‍⚕️ ${doctorName}`;
    }
    
    if (document.getElementById('displayPatientName')) {
        document.getElementById('displayPatientName').innerText = `คนไข้: ${userName || 'ผู้รับบริการ'} (รหัสคิว: ${userId})`;
        fetchDashboardData();
    }
    document.getElementById('tableSearch')?.addEventListener('input', applyFilterAndSearch);
    document.getElementById('statusFilter')?.addEventListener('change', applyFilterAndSearch);
});
