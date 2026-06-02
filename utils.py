"""
أدوات مساعدة مشتركة: تنسيق الردود الرسمية (§19)، استخراج المستخدم الهدف،
المنشن، وصلاحيات تليجرام.
"""
from telegram import Update, User
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

import database as db


def mention(user: User) -> str:
    """منشن HTML آمن لاسم المستخدم."""
    name = (user.full_name or "عضو").replace("<", "").replace(">", "")
    return f'<a href="tg://user?id={user.id}">{name}</a>'


def mention_id(user_id: int, name: str = "عضو") -> str:
    safe = name.replace("<", "").replace(">", "")
    return f'<a href="tg://user?id={user_id}">{safe}</a>'


async def official(text: str) -> str:
    """يضيف رمز البوت [k] قبل النص حسب قالب §19."""
    k = await db.get_bot_key()
    return text.replace("[k]", k)


async def reply_official(update: Update, text: str):
    final = await official(text)
    await update.effective_message.reply_text(final, parse_mode=ParseMode.HTML)


async def resolve_target(update: Update, context: ContextTypes.DEFAULT_TYPE,
                         args_text: str = "") -> tuple[int | None, str]:
    """
    يحدد المستخدم الهدف من:
      1) الرد على رسالة
      2) منشن @username (نصي)
      3) ID رقمي في النص
    يرجّع (user_id, display_name) أو (None, "").
    """
    msg = update.effective_message

    # 1) رد على رسالة
    if msg.reply_to_message and msg.reply_to_message.from_user:
        u = msg.reply_to_message.from_user
        return u.id, u.full_name

    # 2) منشن نصي داخل entities
    if msg.entities:
        for ent in msg.entities:
            if ent.type == "text_mention" and ent.user:
                return ent.user.id, ent.user.full_name

    # 3) ID رقمي
    for token in args_text.split():
        token = token.strip().lstrip("@")
        if token.isdigit():
            uid = int(token)
            try:
                chat_member = await context.bot.get_chat_member(
                    update.effective_chat.id, uid)
                return uid, chat_member.user.full_name
            except Exception:
                return uid, str(uid)

    return None, ""


async def is_tg_admin(update: Update, context: ContextTypes.DEFAULT_TYPE,
                      user_id: int) -> bool:
    """هل المستخدم أدمن تيليجرام في المجموعة؟"""
    try:
        member = await context.bot.get_chat_member(
            update.effective_chat.id, user_id)
        return member.status in ("administrator", "creator")
    except Exception:
        return False


async def bot_has_full_rights(update: Update,
                              context: ContextTypes.DEFAULT_TYPE) -> bool:
    """هل البوت يملك الصلاحيات الكاملة المطلوبة للتفعيل؟"""
    try:
        me = await context.bot.get_chat_member(
            update.effective_chat.id, context.bot.id)
        if me.status != "administrator":
            return False
        return all([
            getattr(me, "can_manage_chat", False),
            getattr(me, "can_delete_messages", False),
            getattr(me, "can_restrict_members", False),
            getattr(me, "can_invite_users", False),
        ])
    except Exception:
        return False
