"""
ตัวเช็คว่าต่อ MongoDB ได้ไหม — รัน: python test_mongo.py
จะบอกชัดๆ ว่าติดตรงไหน
"""
import sys
import os

print("=" * 40)

# 1) เช็คว่ามีไฟล์ secrets.toml ไหม
path = ".streamlit/secrets.toml"
if not os.path.exists(path):
    print("❌ ไม่เจอไฟล์ .streamlit/secrets.toml")
    print("   -> เช็คชื่อไฟล์: ต้องเป็น secrets.toml (ไม่ใช่ secrets.toml.example)")
    sys.exit()
print("✅ เจอไฟล์ secrets.toml")

# 2) อ่านค่า uri
try:
    try:
        import tomllib
        with open(path, "rb") as f:
            cfg = tomllib.load(f)
    except ImportError:
        import toml
        cfg = toml.load(path)
    uri = cfg.get("mongo", {}).get("uri")
except Exception as e:
    print("❌ อ่าน secrets.toml ไม่ได้ (รูปแบบผิด):", e)
    sys.exit()

if not uri:
    print("❌ ไม่เจอ [mongo] uri ในไฟล์")
    sys.exit()
print("✅ เจอ mongo uri แล้ว")

# 3) เช็ค pymongo
try:
    from pymongo import MongoClient
except ImportError:
    print("❌ ยังไม่ได้ติดตั้ง pymongo")
    print("   -> รัน: pip install pymongo")
    sys.exit()
print("✅ ติดตั้ง pymongo แล้ว")

# 4) ลองต่อจริง
try:
    try:
        import certifi
        client = MongoClient(uri, serverSelectionTimeoutMS=5000,
                             tlsCAFile=certifi.where())
    except ImportError:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    print("✅✅✅ ต่อ MongoDB สำเร็จ! ใช้งานได้เลย")
except Exception as e:
    print("❌ ต่อ MongoDB ไม่ติด:")
    print("   ", str(e)[:300])
    print("   -> ถ้าเป็น SSL error: รัน  pip install certifi  แล้วลองใหม่")
    print("   -> ถ้าเป็น auth error: เช็ครหัสผ่าน / Network Access 0.0.0.0/0")

print("=" * 40)
