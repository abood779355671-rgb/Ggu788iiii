"""
§7 — رفع وتنزيل الرتب + التحكم بالرفع.
"""
from telegram import Update
from telegram.ext import ContextTypes

import ranks
import state
from utils import resolve_target, reply_official, mention_id

# (الكلمة, المستوى الممنوح, الرتبة المطلوبة للمنفّذ)
# مرتبة من الأطول للأقصر حتى لا يلتبس "مالك اساسي" مع "مالك"
RAISE_MAP = [
    ("مالك اساسي", ranks.GOWNER, ranks.GOWNER),
    ("dev", ranks.DEV2, ranks.DEVP),
    ("my", ranks.DEV, ranks.DEVP),
    ("مالك", ranks.OWNER, ranks.GOWNER),
    ("مدير", ranks.MOD, ranks.OWNER),
    ("ادمن", ranks.ADMIN, ranks.MOD),
    ("مميز", ranks.PRE, ranks.ADMIN),
]


async def cmd_raise(update: Update, context: ContextTypes.DEFAULT_TYPE,
                    text: str, rank: int) -> bool:
    chat_id = update.effective_chat.id

    if await state.ranks_disabled(chat_id):
        return True  # تجاهل (§2 RULE-05)

    rest = text[len("رفع"):].strip()
    low = rest.lower()

    matched = None
    for kw, level, needed in RAISE_MAP:
        if low.startswith(kw):
            matched = (kw, level, needed)
            arg_text = rest[len(kw):].strip()
            break
    if not matched:
        return False

    _, level, needed = matched
    if rank < needed:
        rn = await ranks.get_rank_name(chat_id, needed)
        await reply_official(update, f"[k] هذا الامر يخص ( {rn} وفوق ) بس")
        return True

    # لا يمكن رفع شخص لرتبة مساوية أو أعلى منك
    if level >= rank:
        await reply_official(update, "[k] مايمديك ترفع احد لرتبتك او اعلى يورع!")
        return True

    uid, name = await resolve_target(update, context, arg_text)
    if not uid:
        await reply_official(update, "[k] رد على رسالة العضو او حط ايديه")
        return True

    await ranks.set_rank(chat_id, uid, level)
    # الرفع يلغي الكتم تلقائياً
    await state.unmute_local(chat_id, uid)
    rn = await ranks.get_rank_name(chat_id, level)
    await reply_official(
        update,
        f"[k] الحلو 「 {mention_id(uid, name)} 」\n[k] رفعته صار {rn}\n[k]")
    return True


async def cmd_demote(update: Update, context: ContextTypes.DEFAULT_TYPE,
                     text: str, rank: int) -> bool:
    chat_id = update.effective_chat.id

    if await state.ranks_disabled(chat_id):
        return True

    rest = text[len("تنزيل"):].strip()
    low = rest.lower()

    # تنزيل الكل
    if low.startswith("الكل"):
        if rank < ranks.OWNER:
            rn = await ranks.get_rank_name(chat_id, ranks.OWNER)
            await reply_official(update, f"[k] هذا الامر يخص ( {rn} وفوق ) بس")
            return True
        uid, name = await resolve_target(update, context, rest[len("الكل"):])
        if not uid:
            await reply_official(update, "[k] رد على رسالة العضو")
            return True
        await ranks.remove_all_ranks(chat_id, uid)
        await reply_official(
            update, f"「 {mention_id(uid, name)} 」\n[k] نزلت كل رتبه\n[k]")
        return True

    matched = None
    for kw, level, needed in RAISE_MAP:
        if low.startswith(kw):
            matched = (kw, level, needed)
            arg_text = rest[len(kw):].strip()
            break
    if not matched:
        return False

    _, level, needed = matched
    if rank < needed:
        rn = await ranks.get_rank_name(chat_id, needed)
        await reply_official(update, f"[k] هذا الامر يخص ( {rn} وفوق ) بس")
        return True

    uid, name = await resolve_target(update, context, arg_text)
    if not uid:
        await reply_official(update, "[k] رد على رسالة العضو او حط ايديه")
        return True

    target_rank = await ranks.get_rank(chat_id, uid)
    if target_rank >= rank:
        await reply_official(update, "[k] مايمديك تنزل احد فوقك يورع!")
        return True

    await ranks.remove_rank(chat_id, uid, level)
    rn = await ranks.get_rank_name(chat_id, level)
    await reply_official(
        update, f"「 {mention_id(uid, name)} 」\n[k] نزلته من {rn}\n[k]")
    return True


async def cmd_toggle_ranks(update: Update, context: ContextTypes.DEFAULT_TYPE,
                           text: str, rank: int) -> bool:
    chat_id = update.effective_chat.id
    if rank < ranks.OWNER:
        rn = await ranks.get_rank_name(chat_id, ranks.OWNER)
        await reply_official(update, f"[k] هذا الامر يخص ( {rn} وفوق ) بس")
        return True

    if text == "تعطيل الرفع":
        await state.set_ranks_disabled(chat_id, True)
        await reply_official(update, "[k] عطلت الرفع في المجموعه\n[k]")
        return True
    if text == "تفعيل الرفع":
        await state.set_ranks_disabled(chat_id, False)
        await reply_official(update, "[k] فعلت الرفع في المجموعه\n[k]")
        return True
    return False
