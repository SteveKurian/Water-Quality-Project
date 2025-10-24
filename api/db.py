import os
from pymongo import MongoClient
try:
    import mongomock
except Exception:
    mongomock = None

def get_db_client():
    """
    If env var USE_MOCK=1 or MONGO_URI not provided, use mongomock.
    Else connect to real MongoDB via MONGO_URI.
    """
    use_mock = os.getenv("USE_MOCK", "1") == "1"
    mongo_uri = os.getenv("MONGO_URI", None)
    if use_mock or (mongo_uri is None and mongomock is not None):
        return mongomock.MongoClient()
    if mongo_uri is None:
        mongo_uri = "mongodb://localhost:27017"
    return MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
