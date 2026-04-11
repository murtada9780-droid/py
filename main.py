from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import os
from user_agents import parse
import httpx

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
        cur.execute("DROP TABLE IF EXISTS visits CASCADE;")
        cur.execute("""
            CREATE TABLE visits (
                id SERIAL PRIMARY KEY,
                gift_slug TEXT,
                ip TEXT,
                location TEXT,
                isp TEXT,
                device_info TEXT, -- الموديل الحقيقي
                system_info TEXT, -- الويندوز أو الـ iOS
                browser_info TEXT, -- كروم أو سفاري
                gpu TEXT, -- كرت الشاشة
                screen_res TEXT, -- دقة الشاشة
                battery TEXT, -- الشحن
                timezone TEXT, -- المنطقة الزمنية
                language TEXT, -- لغة الجهاز
                hardware_details TEXT, -- الرام والمعالج
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Init Error: {e}")

init_db()

@app.post("/api/tracker/track")
async def track_visit(request: Request, data: dict):
    try:
        ip = request.headers.get("x-forwarded-for") or request.client.host
        if "," in ip: ip = ip.split(",")[0].strip()
        
        # تحليل الـ User-Agent لسحب الحقيقة من "كذبة المتصفح"
        ua = parse(data.get("userAgent", ""))
        system = f"{ua.os.family} {ua.os.version_string}"
        device = f"{ua.device.brand or ''} {ua.device.model or 'PC'}".strip()
        browser = f"{ua.browser.family} {ua.browser.version_string}"

        # جلب الموقع والـ ISP
        location, isp = "Unknown", "Unknown"
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(f"http://ip-api.com/json/{ip}")
                geo = res.json()
                location = f"{geo.get('city')}, {geo.get('country')}"
                isp = geo.get('isp')
        except: pass

        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO visits (gift_slug, ip, location, isp, device_info, system_info, browser_info, gpu, screen_res, battery, timezone, language, hardware_details)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data.get("giftId"), ip, location, isp, device, system, browser,
            data.get("gpu"), data.get("screen"), data.get("battery"),
            data.get("timezone"), data.get("language"),
            f"Cores: {data.get('cores')} | RAM: {data.get('ram')}GB"
        ))
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "msg": str(e)}

@app.get("/api/tracker/logs")
async def get_logs():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("SELECT * FROM visits ORDER BY created_at DESC")
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return [dict(zip(columns, r)) for r in rows]
    except: return []
