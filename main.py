from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
import os
from user_agents import parse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_URL = os.environ.get("DATABASE_URL")

def init_db():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        # هذي الحركة بديلة للـ Shell: تمسح القديم وتسوي الجديد
        # ملاحظة: بعد أول تشغيل ناجح، تقدر تحذف سطر DROP TABLE لو تبي
        cur.execute("DROP TABLE IF EXISTS visits;") 
        cur.execute("""
            CREATE TABLE visits (
                id SERIAL PRIMARY KEY,
                gift_slug TEXT NOT NULL,
                ip_address TEXT,
                device TEXT,
                browser TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Database upgraded to Pro version.")
    except Exception as e:
        print(f"❌ DB Error: {e}")

init_db()

@app.post("/api/tracker/track")
async def track_visit(request: Request, item: dict):
    try:
        ip = request.headers.get("x-forwarded-for") or request.client.host
        ua_string = request.headers.get("user-agent")
        user_agent = parse(ua_string)
        
        # تحليل بيانات الجهاز والسيستم
        device = f"{user_agent.os.family} ({user_agent.device.family})"
        browser = f"{user_agent.browser.family} {user_agent.browser.version_string}"
        
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO visits (gift_slug, ip_address, device, browser) VALUES (%s, %s, %s, %s)",
            (item.get("giftId"), ip, device, browser)
        )
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/tracker/logs")
async def get_logs():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("SELECT id, gift_slug, ip_address, device, browser, created_at FROM visits ORDER BY created_at DESC")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [{
            "id": r[0], "giftId": r[1], "ip": r[2], 
            "device": r[3], "browser": r[4], "time": str(r[5])
        } for r in rows]
    except Exception as e:
        return []
