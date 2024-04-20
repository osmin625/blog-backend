import contextlib
from pymongo import MongoClient
from core.config import MONGODB_URL

print(MONGODB_URL)
conn = MongoClient(MONGODB_URL)
str_database_name = 'blog'
db = conn.get_database(str_database_name)
str_collection_name = 'users'
collection = db.get_collection(str_collection_name)

def test(db):
    try:
        db.command("ping")
        return {"status": "OK"}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}
print(test(db))
