"""
حالة المجموعات: التفعيل، الصمت، الكتم المحلي/العام، الحظر العام،
أقفال الأوامر (§5)، تعطيل الرفع (§7)، تعطيل الردود.
"""
from database import r


# ── تفعيل المجموعة (§14) ────────────────────────────────
async def is_enabled(chat_id: int) -> bool:
    return (await r().get(f"enable:{chat_id}")) == "1"


async def set_enabled(chat_id: int, val: bool):
    if val:
        await r().set(f"enable:{chat_id}", "1")
    else:
        await r().delete(f"enable:{chat_id}")


# ── وضع الصمت الكامل (mute:Dev) ─────────────────────────
async def is_silent(chat_id: int) -> bool:
    return (await r().get(f"silent:{chat_id}")) == "1"


async def set_silent(chat_id: int, val: bool):
    if val:
        await r().set(f"silent:{chat_id}", "1")
    else:
        await r().delete(f"silent:{chat_id}")


# ── الكتم المحلي ────────────────────────────────────────
async def is_muted_local(chat_id: int, user_id: int) -> bool:
    return (await r().get(f"mute:{chat_id}:{user_id}")) == "1"


async def mute_local(chat_id: int, user_id: int):
    await r().set(f"mute:{chat_id}:{user_id}", "1")


async def unmute_local(chat_id: int, user_id: int):
    await r().delete(f"mute:{chat_id}:{user_id}")


async def list_muted_local(chat_id: int) -> list[int]:
    out = []
    async for key in r().scan_iter(match=f"mute:{chat_id}:*"):
        out.append(int(key.split(":")[2]))
    return out


# ── الكتم العام ─────────────────────────────────────────
async def is_muted_global(user_id: int) -> bool:
    return (await r().get(f"gmute:{user_id}")) == "1"


async def mute_global(user_id: int):
    await r().set(f"gmute:{user_id}", "1")


async def unmute_global(user_id: int):
    await r().delete(f"gmute:{user_id}")


async def list_muted_global() -> list[int]:
    out = []
    async for key in r().scan_iter(match="gmute:*"):
        out.append(int(key.split(":")[1]))
    return out


# ── الحظر العام (§6) ────────────────────────────────────
async def is_gbanned(user_id: int) -> bool:
    return (await r().get(f"gban:{user_id}")) == "1"


async def gban(user_id: int):
    await r().set(f"gban:{user_id}", "1")


async def ungban(user_id: int):
    await r().delete(f"gban:{user_id}")


async def list_gbanned() -> list[int]:
    out = []
    async for key in r().scan_iter(match="gban:*"):
        out.append(int(key.split(":")[1]))
    return out


# ── تعطيل الرفع (§7) ────────────────────────────────────
async def ranks_disabled(chat_id: int) -> bool:
    return (await r().get(f"disableRanks:{chat_id}")) == "1"


async def set_ranks_disabled(chat_id: int, val: bool):
    if val:
        await r().set(f"disableRanks:{chat_id}", "1")
    else:
        await r().delete(f"disableRanks:{chat_id}")


# ── أقفال الأوامر (§5) ──────────────────────────────────
async def lock_command(chat_id: int, command: str, level: int):
    await r().set(f"lock:{chat_id}:{command}", str(level))


async def unlock_command(chat_id: int, command: str):
    await r().delete(f"lock:{chat_id}:{command}")


async def get_lock_level(chat_id: int, command: str) -> int | None:
    val = await r().get(f"lock:{chat_id}:{command}")
    return int(val) if val is not None else None
