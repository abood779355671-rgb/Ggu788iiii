"""
§10 — الأوامر المخصصة (نص ثابت لكلمة معينة).
"""
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

import ranks
from database import r
from utils import reply_official


def _k_cmd(chat_id):  return f"cmd:{chat_id}"
def _k_gcmd():        return "gcmd"


async def find_command(chat_id: int, text: str) -> str | None:
    val = await r().hget(_k_cmd(chat_id), text)
    if val:
        return val
    return await r().hget(_k_gcmd(), text)


async def cmd_add_command(update: Update, context: ContextTypes.DEFAULT_TYPE,
                          text: str, rank: int) -> bool:
    chat_id = update.effective_chat.id

    # اضف امر عام [الأمر] [النص]
    if text.startswith("اضف امر عام "):
        if rank < ranks.DEV:
            await reply_official(update, "[k] هذا الامر يخص ( Myth وفوق ) بس")
            return True
        rest = text[len("اضف امر عام "):].strip()
        parts = rest.split(maxsplit=1)
        if len(parts) < 2:
            await reply_official(update, "[k] الصيغة: اضف امر عام [الامر] [النص]")
            return True
        await r().hset(_k_gcmd(), parts[0], parts[1])
        await reply_official(update, f"[k] اضفت امر عام: {parts[0]}\n[k]")
        return True

    if text.startswith("اضف امر "):
        if rank < ranks.MOD:
            await reply_official(update, "[k] هذا الامر يخص ( المدير وفوق ) بس")
            return True
        rest = text[len("اضف امر "):].strip()
        parts = rest.split(maxsplit=1)
        if len(parts) < 2:
            await reply_official(update, "[k] الصيغة: اضف امر [الامر] [النص]")
            return True
        await r().hset(_k_cmd(chat_id), parts[0], parts[1])
        await reply_official(update, f"[k] اضفت امر: {parts[0]}\n[k]")
        return True
    return False


async def cmd_show_commands(update: Update, context: ContextTypes.DEFAULT_TYPE,
                            text: str, rank: int) -> bool:
    chat_id = update.effective_chat.id
    if text == "الاوامر المضافه":
        keys = await r().hkeys(_k_cmd(chat_id))
        body = "\n".join(f"• {k}" for k in keys) or "لا يوجد"
        await reply_official(update, f"[k] الاوامر المضافه:\n{body}")
        return True
    if text == "الاوامر العامه":
        keys = await r().hkeys(_k_gcmd())
        body = "\n".join(f"• {k}" for k in keys) or "لا يوجد"
        await reply_official(update, f"[k] الاوامر العامه:\n{body}")
        return True
    return False


async def cmd_delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE,
                             text: str, rank: int) -> bool:
    chat_id = update.effective_chat.id
    if text == "مسح الاوامر":
        if rank < ranks.MOD:
            await reply_official(update, "[k] هذا الامر يخص ( المدير وفوق ) بس")
            return True
        await r().delete(_k_cmd(chat_id))
        await reply_official(update, "[k] مسحت كل الاوامر\n[k]")
        return True
    if text.startswith("مسح امر عام "):
        if rank < ranks.DEV:
            await reply_official(update, "[k] هذا الامر يخص ( Myth وفوق ) بس")
            return True
        word = text[len("مسح امر عام "):].strip()
        await r().hdel(_k_gcmd(), word)
        await reply_official(update, f"[k] مسحت الامر العام: {word}\n[k]")
        return True
    if text.startswith("مسح امر "):
        if rank < ranks.MOD:
            await reply_official(update, "[k] هذا الامر يخص ( المدير وفوق ) بس")
            return True
        word = text[len("مسح امر "):].strip()
        await r().hdel(_k_cmd(chat_id), word)
        await reply_official(update, f"[k] مسحت الامر: {word}\n[k]")
        return True
    return False
