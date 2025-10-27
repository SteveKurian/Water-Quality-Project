import os
from pymongo import MongoClient

_DB_NAME = "water_quality_data"
_COLLECTION_NAME = "asv_1"

def _try_import_mongomock():
    try:
        import mongomock  
        return mongomock.MongoClient(), None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"

def get_db():
    mongo_url = os.environ.get("MONGO_URL")
    if mongo_url:
        client = MongoClient(mongo_url)
        return client[_DB_NAME]

    use_mock = os.environ.get("USE_MOCK", "1").strip()  
    if use_mock in ("1", "true", "True"):
        mock_client, err = _try_import_mongomock()
        if mock_client is not None:
            return mock_client[_DB_NAME]
        raise RuntimeError(
            "mongomock is required for in-memory DB but failed to import. "
            "Either install it or set MONGO_URL. Import error was: " + (err or "unknown")
        )

    
    raise RuntimeError(
        "No database configured. Set MONGO_URL for MongoDB or set USE_MOCK=1 (and install mongomock)."
    )

def get_collection():
    return get_db()[_COLLECTION_NAME]