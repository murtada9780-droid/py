from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
import os

app = FastAPI()

# 1. إعدادات الـ CORS عشان فيرسل يقدر يكلم ريندر
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. الحصول على رابط القاعدة من المتغيرات البيئية
DB_URL = os.environ.get("DATABASE_URL")

class TrackData(BaseModel):
    giftId: str
    slug: str = None

# 3. دالة بناء الجدول (تشتغل تلقائياً أول ما يشتغل السيرفر)
def init_db():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS visits (
                id SERIAL PRIMARY KEY,
                gift_slug TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Database Initialized: Table 'visits' is ready.")
    except Exception as e:
        print(f"❌ DB Init Error: {e}")

# استدعاء الدالة عند بدء التشغيل
init_db()

# 4. مسار استقبال الزيارات (POST)
@app.post("/api/tracker/track")
async def track_visit(data: TrackData):
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("INSERT INTO visits (gift_slug) VALUES (%s)", (data.giftId,))
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 5. مسار جلب السجلات لصفحة الأدمين (GET)
@app.get("/api/tracker/logs")
async def get_logs():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("SELECT id, gift_slug, created_at FROM visits ORDER BY created_at DESC")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        # نرجع البيانات بتنسيق يفهمه ملف Analytics.tsx
        return [{"id": r[0], "giftId": r[1], "time": str(r[2])} for r in rows]
    except Exception as e:
        return []

@app.get("/")
def health_check():
    return {"status": "Tracker is Online"}
