"""
§14 — أحداث التفعيل والتعطيل والمغادرة.
"""
import random
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

import ranks
import state
import database as db
from utils import (reply_official, mention, is_tg_admin, bot_has_full_rights)

LEAVE_LINES = ["وداعاً", "بالتوفيق للجميع", "اطلع يا حلو 👋", "مع السلامة"]


async def _notify_dev(context, text):
    grp = await db.get_dev_group()
    if grp:
        try:
            await context.bot.send_message(int(grp), text)
        except Exception:
            pass


async def cmd_enable(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    user = update.effective_user

    # صلاحية: أدمن تيليجرام أو owner_pls
    rank = await ranks.get_rank(chat.id, user.id)
    if rank < ranks.OWNER and not await is_tg_admin(update, context, user.id):
        await reply_official(update, "[k] التفعيل يخص ادمن المجموعه فقط")
        return True

    if not await db.is_service_enabled():
        await reply_official(update, "[k] البوت الخدمي معطّل حالياً من المطور")
        return True

    if await state.is_enabled(chat.id):
        await reply_official(update, "[k] المجموعة مفعلة من قبل يالطيب")
        return True

    if not await bot_has_full_rights(update, context):
        await reply_official(update, "[k] عطيني كل الصلاحيات بعدين ارسل تفعيل")
        return True

    await state.set_enabled(chat.id, True)

    # رفع المنفّذ مالكاً
    await ranks.set_rank(chat.id, user.id, ranks.OWNER)

    # رفع كل أدمن تليجرام لرتبة أدمن
    try:
        admins = await context.bot.get_chat_administrators(chat.id)
        for a in admins:
            if not a.user.is_bot:
                cur = await ranks.get_rank(chat.id, a.user.id)
                if cur < ranks.ADMIN:
                    await ranks.set_rank(chat.id, a.user.id, ranks.ADMIN)
    except Exception:
        pass

    await reply_official(
        update,
        f"[k] من「 {mention(user)} 」\n"
        f"[k] ابشر تم تفعيل المجموعة ورفعت كل الادمن\n[k]")

    await _notify_dev(context, f"تفعيل جديد: {chat.title} ({chat.id})")
    return True


async def cmd_disable(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    user = update.effective_user
    rank = await ranks.get_rank(chat.id, user.id)
    if rank < ranks.OWNER and not await is_tg_admin(update, context, user.id):
        await reply_official(update, "[k] التعطيل يخص ادمن المجموعه فقط")
        return True
    await state.set_enabled(chat.id, False)
    await reply_official(update, "[k] تم تعطيل المجموعة\n[k]")
    await _notify_dev(context, f"تعطيل: {chat.title} ({chat.id})")
    return True


async def cmd_leave(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    user = update.effective_user
    rank = await ranks.get_rank(chat.id, user.id)
    if rank < ranks.OWNER:
        await reply_official(update, "[k] هذا الامر يخص ( المالك وفوق ) بس")
        return True
    await reply_official(update, f"[k] {random.choice(LEAVE_LINES)}\n[k]")
    await _notify_dev(context, f"طُردت من: {chat.title} ({chat.id})")
    try:
        await context.bot.leave_chat(chat.id)
    except Exception:
        pass
    return True
