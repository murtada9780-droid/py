from fastapi import FastAPI, Request, HTTPException, Response, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
import os, json, datetime, logging

app = FastAPI(docs_url=None, redoc_url=None)

# --- إعدادات التحكم ---
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
logger = logging.getLogger("GIFT_SYSTEM")

# --- إدارة الداتا بيس ---
def get_db_conn():
    return psycopg2.connect(DB_URL, sslmode='require')

@app.on_event("startup")
def boot_system():
    conn = get_db_conn()
    cur = conn.cursor()
    # إنشاء جدول بسيط للأرشفة الرسمية فقط
    cur.execute("""
        CREATE TABLE IF NOT EXISTS gift_logs (
            id SERIAL PRIMARY KEY,
            gift_tag TEXT,
            ip_address TEXT,
            answer_provided TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    logger.info("✅ System Cleaned & Ready")

# --- معالجة البيانات الرسمية ---
def log_gift_activity(gift_tag: str, answer: str, ip: str):
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO gift_logs (gift_tag, ip_address, answer_provided)
            VALUES (%s, %s, %s)
        """, (gift_tag, ip, answer))
        conn.commit()
        cur.close()
        conn.close()
        logger.info(f"💾 Gift activity logged for: {gift_tag}")
    except Exception as e:
        logger.error(f"❌ Database error: {str(e)}")

# --- البوابات ---
@app.post("/api/v1/sys/health/sync")
async def inbound_gate(request: Request, bg: BackgroundTasks):
    """
    بوابة استقبال البيانات الرسمية من الهدايا (جواب السر فقط)
    """
    ip = request.headers.get("x-forwarded-for", request.client.host).split(',')[0]
    try:
        # استلام البيانات كـ JSON عادي بدلاً من Base64 المشفر
        data = await request.json()
        gift_tag = data.get("tag", "unknown")
        answer = data.get("answer", "n/a")
        
        # تسجيل النشاط في الخلفية
        bg.add_task(log_gift_activity, gift_tag, answer, ip)
        
        return {"status": "success", "message": "Gift activity tracked"}
    except:
        return {"status": "error", "message": "Invalid format"}

@app.get("/api/v1/sys/health/report")
async def get_report(key: str = Query(None)):
    if key != MASTER_KEY: 
        return Response(status_code=404)
        
    conn = get_db_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM gift_logs ORDER BY created_at DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

@app.get("/")
async def index():
    return {"message": "System is running"}
