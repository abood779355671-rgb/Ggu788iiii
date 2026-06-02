"""
§15 — معلومات المستخدم والمجموعة + إحصائية الرسائل.
"""
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

import ranks
from database import r
from utils import reply_official, mention, resolve_target, mention_id


def _k_msgs(chat_id, uid): return f"msgs:{chat_id}:{uid}"


async def increment_messages(chat_id: int, uid: int):
    await r().incr(_k_msgs(chat_id, uid))


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE,
                 text: str, rank: int) -> bool:
    chat = update.effective_chat
    user = update.effective_user

    if text == "اسمي":
        await reply_official(update, f"[k] اسمك: {user.full_name}")
        return True

    if text == "ايديي":
        await reply_official(update, f"[k] ايديك: <code>{user.id}</code>")
        return True

    if text == "رتبتي":
        rn = await ranks.get_rank_name(chat.id, rank)
        await reply_official(update, f"[k] رتبتك: {rn}")
        return True

    if text == "رتبته":
        uid, name = await resolve_target(update, context, "")
        if not uid:
            await reply_official(update, "[k] رد على رسالة العضو")
            return True
        trank = await ranks.get_rank(chat.id, uid)
        rn = await ranks.get_rank_name(chat.id, trank)
        await reply_official(update, f"[k] رتبة {mention_id(uid, name)}: {rn}")
        return True

    if text in ("رسائلي", "رسايلي"):
        count = (await r().get(_k_msgs(chat.id, user.id))) or "0"
        await reply_official(update, f"[k] عدد رسائلك: {count}")
        return True

    if text == "مسح رسائلي":
        await r().delete(_k_msgs(chat.id, user.id))
        await reply_official(update, "[k] مسحت احصائية رسائلك\n[k]")
        return True

    if text == "معلوماتي":
        rn = await ranks.get_rank_name(chat.id, rank)
        count = (await r().get(_k_msgs(chat.id, user.id))) or "0"
        username = f"@{user.username}" if user.username else "لا يوجد"
        await reply_official(
            update,
            f"[k] معلوماتك:\n"
            f"الاسم: {user.full_name}\n"
            f"اليوزر: {username}\n"
            f"الايدي: <code>{user.id}</code>\n"
            f"الرتبة: {rn}\n"
            f"الرسائل: {count}")
        return True

    if text == "افتاري":
        photos = await context.bot.get_user_profile_photos(user.id, limit=1)
        if photos.total_count:
            await context.bot.send_photo(chat.id, photos.photos[0][-1].file_id)
        else:
            await reply_official(update, "[k] ما لك صورة")
        return True

    if text == "افتار":
        uid, _ = await resolve_target(update, context, "")
        if not uid:
            await reply_official(update, "[k] رد على رسالة العضو")
            return True
        photos = await context.bot.get_user_profile_photos(uid, limit=1)
        if photos.total_count:
            await context.bot.send_photo(chat.id, photos.photos[0][-1].file_id)
        else:
            await reply_official(update, "[k] ما له صورة")
        return True

    if text in ("المجموعه", "المجموعة"):
        count = await context.bot.get_chat_member_count(chat.id)
        await reply_official(
            update,
            f"[k] معلومات المجموعة:\n"
            f"الاسم: {chat.title}\n"
            f"الايدي: <code>{chat.id}</code>\n"
            f"الاعضاء: {count}")
        return True

    return False
