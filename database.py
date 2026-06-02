"""
غلاف بسيط حول Redis (async) مع دوال مساعدة لكل المفاتيح المستخدمة في البوت.
كل المفاتيح منظمة هنا حتى لا تتسرب بنية البيانات لأي مكان آخر.
"""
import redis.asyncio as redis
from config import (
    REDIS_URL, K_BOT_NAME, K_BOT_KEY, K_SOURCE_CHANNEL, K_SOURCE_LINK,
    K_DEV_GROUP, K_DEVP, K_SERVICE_ENABLED, K_DOWNLOAD_ENABLED,
    DEFAULT_BOT_NAME, DEFAULT_BOT_KEY, DEVP_ID,
)

_r: redis.Redis | None = None


def r() -> redis.Redis:
    global _r
    if _r is None:
        _r = redis.from_url(REDIS_URL, decode_responses=True)
    return _r


async def ping() -> bool:
    try:
        return await r().ping()
    except Exception:
        return False


# ── إعدادات المطور العامة ───────────────────────────────
async def get_bot_name() -> str:
    return (await r().get(K_BOT_NAME)) or DEFAULT_BOT_NAME


async def set_bot_name(name: str):
    await r().set(K_BOT_NAME, name)


async def clear_bot_name():
    await r().delete(K_BOT_NAME)


async def get_bot_key() -> str:
    return (await r().get(K_BOT_KEY)) or DEFAULT_BOT_KEY


async def set_bot_key(key: str):
    await r().set(K_BOT_KEY, key)


async def get_devp() -> int:
    val = await r().get(K_DEVP)
    return int(val) if val else DEVP_ID


async def set_devp(uid: int):
    await r().set(K_DEVP, str(uid))


async def get_dev_group() -> str:
    return (await r().get(K_DEV_GROUP)) or ""


async def set_dev_group(chat_id: str):
    await r().set(K_DEV_GROUP, str(chat_id))


async def is_service_enabled() -> bool:
    val = await r().get(K_SERVICE_ENABLED)
    return val != "0"  # مفعّل افتراضياً


async def set_service(enabled: bool):
    await r().set(K_SERVICE_ENABLED, "1" if enabled else "0")


async def is_download_enabled() -> bool:
    val = await r().get(K_DOWNLOAD_ENABLED)
    return val != "0"


async def set_download(enabled: bool):
    await r().set(K_DOWNLOAD_ENABLED, "1" if enabled else "0")


async def get_source_link() -> str:
    return (await r().get(K_SOURCE_LINK)) or ""


async def set_source_link(link: str):
    await r().set(K_SOURCE_LINK, link)


async def get_source_channel() -> str:
    return (await r().get(K_SOURCE_CHANNEL)) or ""


async def set_source_channel(ch: str):
    await r().set(K_SOURCE_CHANNEL, ch)
