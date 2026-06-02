"""
§17 — لوحة تحكم المطور (تعمل من الخاص فقط مع صاحب البوت).
§20 — لا تنفذ أوامر المطور إلا من الخاص مع صاحب البوت.
"""
from telegram import Update
from telegram.constants import ParseMode, ChatType
from telegram.ext import ContextTypes

import database as db
import state
from utils import reply_official


HELP = (
    "لوحة تحكم المطور:\n"
    "• الاحصائيات\n"
    "• اسم البوت / تعيين اسم البوت [الاسم] / مسح اسم البوت\n"
    "• رمز السورس / وضع رمز السورس [الرمز]\n"
    "• مجموعة المطور / وضع مجموعة المطور [الايدي]\n"
    "• تفعيل البوت الخدمي / تعطيل البوت الخدمي\n"
    "• تفعيل التحميل واليوتيوب / تعطيل التحميل واليوتيوب\n"
    "• المستخدمين المحظورين\n"
    "• تغيير المطور الاساسي [الايدي]\n"
)


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    # فقط الخاص ومع صاحب البوت
    if update.effective_chat.type != ChatType.PRIVATE:
        return False
    if update.effective_user.id != await db.get_devp():
        # عضو عادي في الخاص: لا نكشف اللوحة
        return False

    text = (update.effective_message.text or "").strip()

    if text in ("/start", "البداية"):
        await update.effective_message.reply_text(HELP)
        return True

    if text == "الاحصائيات":
        groups = 0
        async for _ in db.r().scan_iter(match="enable:*"):
            groups += 1
        gbanned = len(await state.list_gbanned())
        name = await db.get_bot_name()
        await update.effective_message.reply_text(
            f"احصائيات البوت:\n"
            f"الاسم: {name}\n"
            f"المجموعات المفعّلة: {groups}\n"
            f"المحظورين عام: {gbanned}\n"
            f"الخدمي: {'مفعّل' if await db.is_service_enabled() else 'معطّل'}\n"
            f"التحميل: {'مفعّل' if await db.is_download_enabled() else 'معطّل'}")
        return True

    if text == "اسم البوت":
        await update.effective_message.reply_text(f"اسم البوت: {await db.get_bot_name()}")
        return True

    if text.startswith("تعيين اسم البوت "):
        name = text[len("تعيين اسم البوت "):].strip()
        await db.set_bot_name(name)
        await update.effective_message.reply_text(f"تم تغيير الاسم الى: {name}")
        return True

    if text == "مسح اسم البوت":
        await db.clear_bot_name()
        await update.effective_message.reply_text("رجعت الاسم الافتراضي: رعد")
        return True

    if text == "رمز السورس":
        await update.effective_message.reply_text(f"الرمز: {await db.get_bot_key()}")
        return True

    if text.startswith("وضع رمز السورس "):
        key = text[len("وضع رمز السورس "):].strip()
        await db.set_bot_key(key)
        await update.effective_message.reply_text(f"تم تغيير الرمز الى: {key}")
        return True

    if text == "مجموعة المطور":
        await update.effective_message.reply_text(f"المجموعة: {await db.get_dev_group() or 'غير محددة'}")
        return True

    if text.startswith("وضع مجموعة المطور "):
        gid = text[len("وضع مجموعة المطور "):].strip()
        await db.set_dev_group(gid)
        await update.effective_message.reply_text("تم تعيين مجموعة المطور")
        return True

    if text == "تفعيل البوت الخدمي":
        await db.set_service(True)
        await update.effective_message.reply_text("تم تفعيل البوت الخدمي")
        return True

    if text == "تعطيل البوت الخدمي":
        await db.set_service(False)
        await update.effective_message.reply_text("تم تعطيل البوت الخدمي")
        return True

    if text == "تفعيل التحميل واليوتيوب":
        await db.set_download(True)
        await update.effective_message.reply_text("تم تفعيل التحميل")
        return True

    if text == "تعطيل التحميل واليوتيوب":
        await db.set_download(False)
        await update.effective_message.reply_text("تم تعطيل التحميل")
        return True

    if text == "المستخدمين المحظورين":
        ids = await state.list_gbanned()
        body = "\n".join(str(i) for i in ids) or "لا يوجد"
        await update.effective_message.reply_text(f"المحظورين عام:\n{body}")
        return True

    if text.startswith("تغيير المطور الاساسي "):
        new_id = text[len("تغيير المطور الاساسي "):].strip()
        if new_id.isdigit():
            await db.set_devp(int(new_id))
            await update.effective_message.reply_text("تم تغيير المطور الاساسي")
        else:
            await update.effective_message.reply_text("ارسل ايدي صحيح")
        return True

    return False
