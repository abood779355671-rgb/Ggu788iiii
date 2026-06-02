"""
هرم الصلاحيات (§3) + تخصيص أسماء الرتب (§4).

مستويات الرتب (الأعلى = أقوى):
    8 devp    مطور البوت (صاحب البوت) فقط
    7 dev2    Dev²
    6 dev     Myth
    5 gowner  المالك الأساسي
    4 owner   المالك
    3 mod     المدير
    2 admin   الأدمن
    1 pre     المميز
    0 member  العضو (بدون صلاحية)
"""
from database import r, get_devp

# ── ثوابت المستويات ─────────────────────────────────────
MEMBER = 0
PRE = 1
ADMIN = 2
MOD = 3
OWNER = 4
GOWNER = 5
DEV = 6
DEV2 = 7
DEVP = 8

# الأسماء الافتراضية لكل رتبة
DEFAULT_NAMES = {
    DEVP: "مطور البوت",
    DEV2: "Dev²",
    DEV: "Myth",
    GOWNER: "المالك الاساسي",
    OWNER: "المالك",
    MOD: "المدير",
    ADMIN: "الادمن",
    PRE: "المميز",
    MEMBER: "العضو",
}

# مفاتيح الأسماء المخصصة لكل رتبة (للتخزين)
RANK_KEYS = {
    GOWNER: "gowner",
    OWNER: "owner",
    MOD: "mod",
    ADMIN: "admin",
    PRE: "pre",
    MEMBER: "member",
}


def _rank_key(chat_id: int, user_id: int) -> str:
    return f"rank:{chat_id}:{user_id}"


def _grank_key(user_id: int) -> str:
    """الرتب العامة (Dev / Dev2 / Myth) محفوظة عالمياً عبر كل المجموعات."""
    return f"grank:{user_id}"


async def get_rank(chat_id: int, user_id: int) -> int:
    """يرجّع أعلى رتبة يملكها المستخدم (عامة أو محلية)."""
    if user_id == await get_devp():
        return DEVP

    grank = await r().get(_grank_key(user_id))
    g = int(grank) if grank else 0

    lrank = await r().get(_rank_key(chat_id, user_id))
    l = int(lrank) if lrank else 0

    return max(g, l)


async def set_rank(chat_id: int, user_id: int, level: int):
    """رفع رتبة. الرتب العامة (DEV وفوق) تُحفظ عالمياً، الباقي محلياً."""
    if level >= DEV:
        await r().set(_grank_key(user_id), str(level))
    else:
        await r().set(_rank_key(chat_id, user_id), str(level))


async def remove_rank(chat_id: int, user_id: int, level: int):
    """تنزيل رتبة محددة."""
    if level >= DEV:
        await r().delete(_grank_key(user_id))
    else:
        await r().delete(_rank_key(chat_id, user_id))


async def remove_all_ranks(chat_id: int, user_id: int):
    await r().delete(_rank_key(chat_id, user_id))
    await r().delete(_grank_key(user_id))


async def list_rank(chat_id: int, level: int) -> list[int]:
    """قائمة المستخدمين بمستوى معيّن في المجموعة."""
    result = []
    if level >= DEV:
        async for key in r().scan_iter(match="grank:*"):
            val = await r().get(key)
            if val and int(val) == level:
                result.append(int(key.split(":")[1]))
    else:
        async for key in r().scan_iter(match=f"rank:{chat_id}:*"):
            val = await r().get(key)
            if val and int(val) == level:
                result.append(int(key.split(":")[2]))
    return result


# ── تخصيص الأسماء (§4) ──────────────────────────────────
async def get_rank_name(chat_id: int, level: int) -> str:
    rk = RANK_KEYS.get(level)
    if rk:
        custom = await r().get(f"rankname:{chat_id}:{rk}")
        if custom:
            return custom
    return DEFAULT_NAMES.get(level, "عضو")


async def set_rank_name(chat_id: int, level: int, name: str):
    rk = RANK_KEYS.get(level)
    if rk:
        await r().set(f"rankname:{chat_id}:{rk}", name)


async def clear_rank_name(chat_id: int, level: int):
    rk = RANK_KEYS.get(level)
    if rk:
        await r().delete(f"rankname:{chat_id}:{rk}")


# ── دوال التحقق (مثل devp_pls / mod_pls ...) ─────────────
async def has_rank(chat_id: int, user_id: int, required: int) -> bool:
    return (await get_rank(chat_id, user_id)) >= required
