import motor.motor_asyncio

from app.config import settings

_client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGO_URI)
_db = _client[settings.MONGO_DB]


def get_conversations_collection() -> motor.motor_asyncio.AsyncIOMotorCollection:
    return _db["conversations"]
