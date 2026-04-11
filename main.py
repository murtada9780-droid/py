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
        cur.execute("DROP TABLE IF EXISTS visits CASCADE;") # مسح شامل للتحديث
        cur.execute("""
            CREATE TABLE visits (
                id SERIAL PRIMARY KEY,
                gift_slug TEXT,
                ip TEXT,
                location TEXT,
                isp TEXT,
                os_system TEXT,
                device_model TEXT,
                browser TEXT,
                screen_res TEXT,
                cores TEXT,
                memory TEXT,
                battery TEXT,
                connection_type TEXT,
                is_vpn BOOLEAN,
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
        # 1. سحب الـ IP ومعلومات الشبكة
        ip = request.headers.get("x-forwarded-for") or request.client.host
        if "," in ip: ip = ip.split(",")[0].strip()
        
        # 2. تحليل الموقع والـ VPN
        geo_data = {"city": "Unknown", "country": "Unknown", "isp": "Unknown", "proxy": False}
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(f"http://ip-api.com/json/{ip}?fields=status,message,country,city,isp,proxy")
                if res.status_code == 200: geo_data = res.json()
        except: pass

        # 3. حفظ البيانات في القاعدة
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO visits (
                gift_slug, ip, location, isp, os_system, device_model, 
                browser, screen_res, cores, memory, battery, connection_type, is_vpn
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data.get("giftId"),
            ip,
            f"{geo_data.get('city')}, {geo_data.get('country')}",
            geo_data.get("isp"),
            data.get("os"),
            data.get("device"),
            data.get("browser"),
            data.get("screen"),
            str(data.get("cores")),
            str(data.get("ram")),
            data.get("battery"),
            data.get("connection"),
            geo_data.get("proxy", False)
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
