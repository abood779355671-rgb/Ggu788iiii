"""
§13 — الترحيب والقوانين.
"""
from datetime import datetime
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

import ranks
from database import r
from utils import reply_official, mention

DEFAULT_WELCOME = (
    "لا تُسِئ اللفظ وإن ضَاق عليك الرَّد\n"
    "ɴᴀᴍᴇ ⌯ {الاسم}\n"
    "ᴜѕᴇʀɴᴀᴍᴇ ⌯ {اليوزر}\n"
    "𝖣𝖺𝗍𝖾 ⌯ {التاريخ}"
)


def _k_welcome(chat_id): return f"welcome:{chat_id}"
def _k_rules(chat_id):   return f"rules:{chat_id}"
def _k_welcome_on(chat_id): return f"welcome_on:{chat_id}"


def _fill(template: str, user) -> str:
    username = f"@{user.username}" if user.username else "لا يوجد"
    date = datetime.now().strftime("%Y-%m-%d")
    safe_name = (user.full_name or "عضو").replace("<", "").replace(">", "")
    return (template.replace("{الاسم}", safe_name)
                    .replace("{اليوزر}", username)
                    .replace("{التاريخ}", date))


# ── أحداث الدخول/الخروج (§14) ───────────────────────────
async def on_member_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if (await r().get(_k_welcome_on(chat_id))) != "1":
        return
    template = (await r().get(_k_welcome(chat_id))) or DEFAULT_WELCOME
    for member in update.message.new_chat_members:
        if member.is_bot:
            continue
        text = _fill(template, member)
        await context.bot.send_message(chat_id, text, parse_mode=ParseMode.HTML)


async def on_member_leave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    member = update.message.left_chat_member
    if member and not member.is_bot:
        await context.bot.send_message(
            chat_id, f"{mention(member)} غادر المجموعة، بالتوفيق",
            parse_mode=ParseMode.HTML)


# ── أوامر الترحيب ───────────────────────────────────────
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE,
                 text: str, rank: int) -> bool:
    chat_id = update.effective_chat.id

    # إلغاء عملية الإدخال الجارية
    if text == "الغاء" and context.user_data.get("setting"):
        context.user_data.pop("setting", None)
        await reply_official(update, "[k] تم الالغاء\n[k]")
        return True

    if text in ("وضع الترحيب", "ضع الترحيب"):
        if rank < ranks.ADMIN:
            await reply_official(update, "[k] هذا الامر يخص ( الادمن وفوق ) بس")
            return True
        context.user_data["setting"] = "welcome"
        await reply_official(
            update,
            "[k] ارسل نص الترحيب\n[k] المتغيرات: {الاسم} {اليوزر} {التاريخ}")
        return True

    if text == "الترحيب":
        if rank < ranks.ADMIN:
            await reply_official(update, "[k] هذا الامر يخص ( الادمن وفوق ) بس")
            return True
        cur = (await r().get(_k_welcome(chat_id))) or DEFAULT_WELCOME
        await reply_official(update, f"[k] الترحيب الحالي:\n{cur}")
        return True

    if text == "مسح الترحيب":
        if rank < ranks.ADMIN:
            await reply_official(update, "[k] هذا الامر يخص ( الادمن وفوق ) بس")
            return True
        await r().delete(_k_welcome(chat_id))
        await r().delete(_k_welcome_on(chat_id))
        await reply_official(update, "[k] مسحت الترحيب\n[k]")
        return True

    if text == "وضع قوانين":
        if rank < ranks.ADMIN:
            await reply_official(update, "[k] هذا الامر يخص ( الادمن وفوق ) بس")
            return True
        context.user_data["setting"] = "rules"
        await reply_official(update, "[k] ارسل نص القوانين")
        return True

    if text in ("القوانين", "قوانين"):
        cur = await r().get(_k_rules(chat_id))
        if not cur:
            await reply_official(update, "[k] لا يوجد قوانين")
            return True
        await reply_official(update, f"[k] القوانين:\n{cur}")
        return True

    if text == "مسح القوانين":
        if rank < ranks.ADMIN:
            await reply_official(update, "[k] هذا الامر يخص ( الادمن وفوق ) بس")
            return True
        await r().delete(_k_rules(chat_id))
        await reply_official(update, "[k] مسحت القوانين\n[k]")
        return True

    return False


async def handle_setting_step(update: Update,
                              context: ContextTypes.DEFAULT_TYPE) -> bool:
    """استقبال نص الترحيب/القوانين بعد الأمر."""
    setting = context.user_data.get("setting")
    if not setting:
        return False
    chat_id = update.effective_chat.id
    msg = update.effective_message
    if (msg.text or "").strip() == "الغاء":
        context.user_data.pop("setting", None)
        await reply_official(update, "[k] تم الالغاء\n[k]")
        return True
    content = msg.text or ""
    if setting == "welcome":
        await r().set(_k_welcome(chat_id), content)
        await r().set(_k_welcome_on(chat_id), "1")
        await reply_official(update, "[k] تم حفظ الترحيب وتفعيله\n[k]")
    elif setting == "rules":
        await r().set(_k_rules(chat_id), content)
        await reply_official(update, "[k] تم حفظ القوانين\n[k]")
    context.user_data.pop("setting", None)
    return True
