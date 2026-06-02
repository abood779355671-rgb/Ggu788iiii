"""
نقطة الدخول والموجّه الرئيسي (§18 — منطق معالجة كل رسالة مرتب بالأولوية).
"""
import logging

from telegram import Update
from telegram.constants import ChatType
from telegram.ext import (Application, MessageHandler, CommandHandler,
                          filters, ContextTypes)

import config
import database as db
import state
import ranks
from personality import emotional_reply, name_reply

from handlers import (mute_and_gban as mg, rank_actions as ra,
                      get_ranks as gr, custom_filter as cf,
                      custom_command as cc, fun, welcome_and_rules as wr,
                      group_update as gu, user_info as ui, dev_panel as dp)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO)
logger = logging.getLogger("raad-bot")


async def dispatch_system(update, context, text, rank) -> bool:
    """يجرّب أوامر النظام بالترتيب. يرجّع True لو نُفّذ أمر."""

    # ── كتم / حظر (§6) ──────────────────────────────────
    if text == "كتم عام" or text.startswith("كتم عام"):
        return await mg.cmd_gmute(update, context, text[len("كتم عام"):].strip(), rank)
    if text == "الغاء الكتم العام" or text.startswith("الغاء الكتم العام"):
        return await mg.cmd_ungmute(update, context, text, rank)
    if text == "الغاء الكتم" or text.startswith("الغاء الكتم"):
        return await mg.cmd_unmute(update, context, text, rank)
    if text == "كتم" or text.startswith("كتم"):
        return await mg.cmd_mute(update, context, text[len("كتم"):].strip(), rank)
    if text == "حظر عام" or text.startswith("حظر عام"):
        return await mg.cmd_gban(update, context, text[len("حظر عام"):].strip(), rank)
    if text == "الغاء الحظر العام" or text.startswith("الغاء الحظر العام"):
        return await mg.cmd_ungban(update, context, text, rank)

    # ── التحكم بالرفع (§7) ───────────────────────────────
    if text in ("تعطيل الرفع", "تفعيل الرفع"):
        return await ra.cmd_toggle_ranks(update, context, text, rank)

    # ── رفع / تنزيل (§7) — قبل ألقاب المتعة ──────────────
    if text.startswith("رفع "):
        if await ra.cmd_raise(update, context, text, rank):
            return True
        return await fun.handle(update, context, text, rank)
    if text.startswith("تنزيل "):
        if await ra.cmd_demote(update, context, text, rank):
            return True
        return await fun.handle(update, context, text, rank)

    # ── عرض الرتب والقوائم (§8) ──────────────────────────
    if await gr.cmd_list_ranks(update, context, text, rank):
        return True

    # ── تخصيص أسماء الرتب (§4) ───────────────────────────
    if text.startswith("تعيين اسم") or text.startswith("مسح اسم"):
        if await gr.cmd_custom_rank(update, context, text, rank):
            return True

    # ── الردود المخصصة (§9) ──────────────────────────────
    if text in ("اضف رد", "اضف ردي", "اضف رد مميز", "اضف رد عام"):
        return await cf.cmd_add_filter(update, context, text, rank)
    if text in ("الردود", "الردود المميزه", "الردود العامه", "ردي"):
        return await cf.cmd_show_filters(update, context, text, rank)
    if text.startswith("مسح رد") or text == "مسح الردود" or text == "مسح ردي":
        return await cf.cmd_delete_filter(update, context, text, rank)
    if text.startswith("تعطيل ردود") or text.startswith("تفعيل ردود") \
            or text in ("تعطيل الردود", "تفعيل الردود"):
        return await cf.cmd_toggle_filters(update, context, text, rank)

    # ── الأوامر المخصصة (§10) ────────────────────────────
    if text.startswith("اضف امر"):
        return await cc.cmd_add_command(update, context, text, rank)
    if text in ("الاوامر المضافه", "الاوامر العامه"):
        return await cc.cmd_show_commands(update, context, text, rank)
    if text.startswith("مسح امر") or text == "مسح الاوامر":
        return await cc.cmd_delete_command(update, context, text, rank)

    # ── الترحيب والقوانين (§13) ──────────────────────────
    if await wr.handle(update, context, text, rank):
        return True

    # ── معلومات المستخدم (§15) ───────────────────────────
    if await ui.handle(update, context, text, rank):
        return True

    # ── ألقاب المتعة (§11) ───────────────────────────────
    if await fun.handle(update, context, text, rank):
        return True

    return False


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg:
        return

    # ── الخاص: لوحة المطور (§17/§20) ─────────────────────
    if update.effective_chat.type == ChatType.PRIVATE:
        await dp.handle(update, context)
        return

    if update.effective_chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        return

    chat_id = update.effective_chat.id
    user = update.effective_user
    if user is None:
        return
    raw = (msg.text or "").strip()

    bot_name = await db.get_bot_name()

    # [1] هل المجموعة مفعّلة؟ — "تفعيل" لها منطق خاص
    enabled = await state.is_enabled(chat_id)
    if raw in ("تفعيل", f"{bot_name} تفعيل"):
        await gu.cmd_enable(update, context)
        return
    if not enabled:
        return  # تجاهل تام

    # عدّاد الرسائل
    await ui.increment_messages(chat_id, user.id)

    # [2] محظور عام؟ → طرد فوري
    if await state.is_gbanned(user.id):
        try:
            await context.bot.ban_chat_member(chat_id, user.id)
        except Exception:
            pass
        return

    # [3] مكتوم (محلي أو عام)؟ → حذف الرسالة بصمت
    if await state.is_muted_local(chat_id, user.id) or \
            await state.is_muted_global(user.id):
        try:
            await msg.delete()
        except Exception:
            pass
        return

    rank = await ranks.get_rank(chat_id, user.id)

    # [4] وضع الصمت الكامل؟ → تجاهل غير الإداريين
    if await state.is_silent(chat_id) and rank < ranks.ADMIN:
        return

    # [5] وضع إضافة رد / وضع ترحيب جارٍ
    if await cf.handle_addfilter_step(update, context):
        return
    if await wr.handle_setting_step(update, context):
        return

    if not raw:
        return

    # [6] يبدأ باسم البوت؟ → احذف الاسم
    text = raw
    if text.startswith(bot_name + " "):
        text = text[len(bot_name) + 1:].strip()
    elif text == bot_name:
        await msg.reply_text(name_reply())
        return

    # تعطيل/مغادرة (§14)
    if text == "تعطيل":
        await gu.cmd_disable(update, context)
        return
    if text in ("اطلعي", "اطلع"):
        await gu.cmd_leave(update, context)
        return

    # [7] أمر مقفول؟ (§5)
    first = text.split()[0] if text.split() else text
    lock_level = await state.get_lock_level(chat_id, first)
    if lock_level is not None and rank < (ranks.GOWNER - lock_level):
        # المستوى 0=gowner، 1=owner، 2=mod، 3=admin، 4=pre حسب §5
        return

    # [8] أوامر النظام (أعلى أولوية)
    if await dispatch_system(update, context, text, rank):
        return

    # الردود العاطفية (§1)
    emo = emotional_reply(text)
    if emo:
        await msg.reply_text(emo)
        return
    if text in ("بوت", bot_name):
        await msg.reply_text(name_reply())
        return

    # الأوامر المخصصة الثابتة (§10)
    custom = await cc.find_command(chat_id, text)
    if custom:
        await msg.reply_text(custom)
        return

    # الردود المخصصة (محلية → أعضاء → عامة) (§9)
    if (await db.r().get(f"filters_off:{chat_id}")) != "1":
        reply_data = await cf.find_reply(chat_id, user.id, text)
        if reply_data:
            await cf.send_stored(update, context, reply_data)
            return

    # [9] لا تطابق → تجاهل تام


async def on_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await state.is_enabled(update.effective_chat.id):
        await wr.on_member_join(update, context)


async def on_left_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await state.is_enabled(update.effective_chat.id):
        await wr.on_member_leave(update, context)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == ChatType.PRIVATE:
        await dp.handle(update, context)


def main():
    if not config.BOT_TOKEN:
        raise SystemExit("ضع TELEGRAM_BOT_TOKEN في ملف .env اولاً")

    app = Application.builder().token(config.BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS, on_new_member))
    app.add_handler(MessageHandler(
        filters.StatusUpdate.LEFT_CHAT_MEMBER, on_left_member))
    # كل الرسائل (نص ووسائط) ما عدا تحديثات الحالة
    app.add_handler(MessageHandler(
        ~filters.StatusUpdate.ALL, on_text))

    logger.info("البوت يعمل الآن...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
