"""
§11 — ألقاب المتعة. كل لقب: رفع (رد) / تنزيل (رد) / قائمة / مسح القائمة.
"""
from telegram import Update
from telegram.ext import ContextTypes

import ranks
from database import r
from utils import resolve_target, reply_official, mention_id

# (المفتاح, الإيموجي, اسم مفرد, اسم الجمع في القائمة)
TITLES = [
    ("كيك", "🍰", "كيك", "الكيك"),
    ("عسل", "🍯", "عسل", "العسل"),
    ("نصاب", "💩", "نصاب", "النصابين"),
    ("حمار", "🐴", "حمار", "الحمير"),
    ("بقرة", "🐮", "بقرة", "البقر"),
    ("كلب", "🐶", "كلب", "الكلاب"),
    ("قرد", "🐒", "قرد", "القرود"),
    ("تيس", "🐐", "تيس", "التيس"),
    ("ثور", "🐂", "ثور", "الثور"),
    ("هكر", "💻", "هكر", "الهكر"),
    ("دجاجه", "🐔", "دجاجه", "الدجاج"),
    ("ملكه", "👑", "ملكه", "الهطوف"),
    ("صياد", "🎣", "صياد", "الصيادين"),
    ("خروف", "🐑", "خروف", "الخرفان"),
]


def _k(chat_id, key):  return f"fun:{chat_id}:{key}"


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE,
                 text: str, rank: int) -> bool:
    chat_id = update.effective_chat.id

    for key, emoji, single, plural in TITLES:
        # رفع
        if text == f"رفع {key}":
            uid, name = await resolve_target(update, context, "")
            if not uid:
                await reply_official(update, "[k] رد على رسالة العضو")
                return True
            await r().sadd(_k(chat_id, key), uid)
            await reply_official(
                update, f"{emoji} 「 {mention_id(uid, name)} 」\n[k] صار {single}\n[k]")
            return True
        # تنزيل
        if text == f"تنزيل {key}":
            uid, name = await resolve_target(update, context, "")
            if not uid:
                await reply_official(update, "[k] رد على رسالة العضو")
                return True
            await r().srem(_k(chat_id, key), uid)
            await reply_official(
                update, f"「 {mention_id(uid, name)} 」\n[k] نزلته من {single}\n[k]")
            return True
        # قائمة
        if text == f"قائمة {plural}":
            uids = await r().smembers(_k(chat_id, key))
            if not uids:
                await reply_official(update, f"{emoji} قائمة {plural}\n[k] لا يوجد")
                return True
            lines = [f"{emoji} قائمة {plural}\n"]
            for i, u in enumerate(uids, 1):
                lines.append(f"{i} ⌯ {mention_id(int(u))}")
            await reply_official(update, "\n".join(lines))
            return True
        # مسح القائمة
        if text == f"مسح قائمة {plural}":
            if rank < ranks.ADMIN:
                await reply_official(update, "[k] هذا الامر يخص ( الادمن وفوق ) بس")
                return True
            await r().delete(_k(chat_id, key))
            await reply_official(update, f"[k] مسحت قائمة {plural}\n[k]")
            return True

    # ❤️ من قلبي (صيغة مختلفة)
    if text == "رفع لقلبي":
        uid, name = await resolve_target(update, context, "")
        if uid:
            await r().sadd(_k(chat_id, "قلبي"), uid)
            await reply_official(
                update, f"❤️ 「 {mention_id(uid, name)} 」\n[k] صار من قلبي\n[k]")
            return True
    if text == "تنزيل من قلبي":
        uid, name = await resolve_target(update, context, "")
        if uid:
            await r().srem(_k(chat_id, "قلبي"), uid)
            await reply_official(
                update, f"「 {mention_id(uid, name)} 」\n[k] نزلته من قلبك\n[k]")
            return True
    return False
