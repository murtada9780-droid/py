from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
import os

app = FastAPI()

# تفعيل الـ CORS عشان موقعك في فيرسل يقدر يرسل بيانات هنا
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # تقدر تحدد رابط موقعك هنا للأمان
    allow_methods=["*"],
    allow_headers=["*"],
)

# رابط قاعدة البيانات (بنجيبه من ريندر بعد شوي)
DB_URL = os.environ.get("DATABASE_URL")

class TrackData(BaseModel):
    giftId: str
    slug: str = None

@app.post("/api/tracker/track")
async def track_visit(data: TrackData):
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        # تأكد إن عندك جدول اسمه visits وفيه عمود اسمه gift_slug
        # أو عدل اسم الجدول والأعمدة حسب اللي عندك
        cur.execute("INSERT INTO visits (gift_slug) VALUES (%s)", (data.giftId,))
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/")
def home():
    return {"message": "Tracker is running!"}