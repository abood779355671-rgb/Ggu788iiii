"""
§9 / §10 — نظام الردود المخصصة:
ردود المجموعة، ردود الأعضاء، الردود المميزة، الردود العامة.
يدعم: نص، صورة، فيديو، صوت، ملف، ستيكر، انيميشن.
متغيرات: <USER_ID> <USER_NAME> <USER_USERNAME> <USER_MENTION>
"""
import json
from telegram import Update, Message
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

import ranks
import state
from database import r
from utils import reply_official, mention


# ── مفاتيح ──────────────────────────────────────────────
def _k_group(chat_id):    return f"filter:{chat_id}"
def _k_member(chat_id, uid): return f"filter_member:{chat_id}:{uid}"
def _k_premium(chat_id):  return f"filter_pre:{chat_id}"
def _k_global():          return "gfilter"


# ── حفظ/استرجاع محتوى الرسالة ───────────────────────────
def capture_message(msg: Message) -> dict:
    """يحوّل رسالة إلى قاموس قابل للتخزين (نص أو وسائط)."""
    if msg.photo:
        return {"type": "photo", "file_id": msg.photo[-1].file_id,
                "caption": msg.caption or ""}
    if msg.video:
        return {"type": "video", "file_id": msg.video.file_id,
                "caption": msg.caption or ""}
    if msg.animation:
        return {"type": "animation", "file_id": msg.animation.file_id,
                "caption": msg.caption or ""}
    if msg.voice:
        return {"type": "voice", "file_id": msg.voice.file_id}
    if msg.audio:
        return {"type": "audio", "file_id": msg.audio.file_id}
    if msg.sticker:
        return {"type": "sticker", "file_id": msg.sticker.file_id}
    if msg.document:
        return {"type": "document", "file_id": msg.document.file_id,
                "caption": msg.caption or ""}
    return {"type": "text", "text": msg.text or ""}


def _apply_vars(text: str, update: Update) -> str:
    u = update.effective_user
    return (text.replace("<USER_ID>", str(u.id))
                .replace("<USER_NAME>", u.full_name or "")
                .replace("<USER_USERNAME>", f"@{u.username}" if u.username else "")
                .replace("<USER_MENTION>", mention(u)))


async def send_stored(update: Update, context: ContextTypes.DEFAULT_TYPE,
                      data: dict):
    chat_id = update.effective_chat.id
    t = data.get("type", "text")
    cap = _apply_vars(data.get("caption", ""), update) or None
    if t == "text":
        await context.bot.send_message(
            chat_id, _apply_vars(data.get("text", ""), update),
            parse_mode=ParseMode.HTML)
    elif t == "photo":
        await context.bot.send_photo(chat_id, data["file_id"], caption=cap,
                                     parse_mode=ParseMode.HTML)
    elif t == "video":
        await context.bot.send_video(chat_id, data["file_id"], caption=cap,
                                     parse_mode=ParseMode.HTML)
    elif t == "animation":
        await context.bot.send_animation(chat_id, data["file_id"], caption=cap,
                                         parse_mode=ParseMode.HTML)
    elif t == "voice":
        await context.bot.send_voice(chat_id, data["file_id"])
    elif t == "audio":
        await context.bot.send_audio(chat_id, data["file_id"])
    elif t == "sticker":
        await context.bot.send_sticker(chat_id, data["file_id"])
    elif t == "document":
        await context.bot.send_document(chat_id, data["file_id"], caption=cap,
                                        parse_mode=ParseMode.HTML)


# ── إيجاد الرد المناسب (يُستدعى من الموجّه) ──────────────
async def find_reply(chat_id: int, user_id: int, text: str) -> dict | None:
    # 1) ردود المجموعة المحلية
    val = await r().hget(_k_group(chat_id), text)
    if val:
        return json.loads(val)
    # 2) ردود الأعضاء (الشخصية)
    val = await r().hget(_k_member(chat_id, user_id), text)
    if val:
        return json.loads(val)
    # 3) الردود المميزة
    val = await r().hget(_k_premium(chat_id), text)
    if val:
        return json.loads(val)
    # 4) الردود العامة (إن لم تكن معطّلة في المجموعة)
    if not await state_filters_disabled(chat_id):
        val = await r().hget(_k_global(), text)
        if val:
            return json.loads(val)
    return None


async def state_filters_disabled(chat_id: int) -> bool:
    return (await r().get(f"dev_filters_off:{chat_id}")) == "1"


# ── بدء عملية إضافة رد (محادثة) ─────────────────────────
async def cmd_add_filter(update: Update, context: ContextTypes.DEFAULT_TYPE,
                         text: str, rank: int) -> bool:
    chat_id = update.effective_chat.id

    scopes = {
        "اضف رد مميز": ("premium", ranks.PRE),
        "اضف رد عام": ("global", ranks.DEV),
        "اضف ردي": ("member", ranks.MEMBER),
        "اضف رد": ("group", ranks.MOD),
    }
    scope = None
    for key, (sc, needed) in scopes.items():
        if text == key:
            scope, need = sc, needed
            break
    if scope is None:
        return False

    if rank < need:
        rn = await ranks.get_rank_name(chat_id, need)
        await reply_official(update, f"[k] هذا الامر يخص ( {rn} وفوق ) بس")
        return True

    context.user_data["addfilter"] = {"scope": scope, "step": "word"}
    await reply_official(update, "[k] ارسل الكلمة المشغّلة للرد\n[k] (او ارسل الغاء)")
    return True


async def handle_addfilter_step(update: Update,
                                context: ContextTypes.DEFAULT_TYPE) -> bool:
    """يُستدعى من الموجّه عندما يكون المستخدم في وضع إضافة رد."""
    pending = context.user_data.get("addfilter")
    if not pending:
        return False

    msg = update.effective_message
    if (msg.text or "").strip() == "الغاء":
        context.user_data.pop("addfilter", None)
        await reply_official(update, "[k] تم الغاء العمليه\n[k]")
        return True

    chat_id = update.effective_chat.id
    uid = update.effective_user.id

    if pending["step"] == "word":
        word = (msg.text or "").strip()
        if not word:
            await reply_official(update, "[k] لازم ترسل نص للكلمة")
            return True
        pending["word"] = word
        pending["step"] = "reply"
        await reply_official(update, "[k] الحين ارسل الرد (نص/صورة/فيديو/صوت/ملف/ستيكر)")
        return True

    if pending["step"] == "reply":
        data = capture_message(msg)
        word = pending["word"]
        scope = pending["scope"]
        if scope == "group":
            await r().hset(_k_group(chat_id), word, json.dumps(data))
        elif scope == "member":
            await r().hset(_k_member(chat_id, uid), word, json.dumps(data))
        elif scope == "premium":
            await r().hset(_k_premium(chat_id), word, json.dumps(data))
        elif scope == "global":
            await r().hset(_k_global(), word, json.dumps(data))
        context.user_data.pop("addfilter", None)
        await reply_official(update, f"[k] تم اضافة الرد على: {word}\n[k]")
        return True

    return False


# ── عرض / حذف ───────────────────────────────────────────
async def cmd_show_filters(update: Update, context: ContextTypes.DEFAULT_TYPE,
                           text: str, rank: int) -> bool:
    chat_id = update.effective_chat.id
    uid = update.effective_user.id

    targets = {
        "الردود": _k_group(chat_id),
        "الردود المميزه": _k_premium(chat_id),
        "الردود العامه": _k_global(),
        "ردي": _k_member(chat_id, uid),
    }
    if text not in targets:
        return False
    keys = await r().hkeys(targets[text])
    if not keys:
        await reply_official(update, f"[k] {text}\n[k] لا يوجد")
        return True
    listing = "\n".join(f"• {w}" for w in keys)
    await reply_official(update, f"[k] {text}:\n{listing}")
    return True


async def cmd_delete_filter(update: Update, context: ContextTypes.DEFAULT_TYPE,
                            text: str, rank: int) -> bool:
    chat_id = update.effective_chat.id
    uid = update.effective_user.id

    if text == "مسح الردود":
        if rank < ranks.MOD:
            await reply_official(update, "[k] هذا الامر يخص ( المدير وفوق ) بس")
            return True
        await r().delete(_k_group(chat_id))
        await reply_official(update, "[k] مسحت كل ردود المجموعه\n[k]")
        return True

    if text == "مسح الردود العامه":
        if rank < ranks.DEV:
            await reply_official(update, "[k] هذا الامر يخص ( Myth وفوق ) بس")
            return True
        await r().delete(_k_global())
        await reply_official(update, "[k] مسحت الردود العامه\n[k]")
        return True

    if text == "مسح ردي":
        await r().delete(_k_member(chat_id, uid))
        await reply_official(update, "[k] مسحت ردودك الشخصيه\n[k]")
        return True

    for prefix, key, needed in [
        ("مسح رد مميز ", _k_premium(chat_id), ranks.PRE),
        ("مسح رد عام ", _k_global(), ranks.DEV),
        ("مسح رد ", _k_group(chat_id), ranks.MOD),
    ]:
        if text.startswith(prefix):
            if rank < needed:
                rn = await ranks.get_rank_name(chat_id, needed)
                await reply_official(update, f"[k] هذا الامر يخص ( {rn} وفوق ) بس")
                return True
            word = text[len(prefix):].strip()
            await r().hdel(key, word)
            await reply_official(update, f"[k] مسحت الرد: {word}\n[k]")
            return True
    return False


async def cmd_toggle_filters(update: Update, context: ContextTypes.DEFAULT_TYPE,
                             text: str, rank: int) -> bool:
    chat_id = update.effective_chat.id
    if text in ("تعطيل الردود", "تفعيل الردود",
                "تعطيل ردود المطور", "تفعيل ردود المطور",
                "تعطيل ردود الاعضاء", "تفعيل ردود الاعضاء"):
        if rank < ranks.ADMIN:
            await reply_official(update, "[k] هذا الامر يخص ( الادمن وفوق ) بس")
            return True
        if text == "تعطيل الردود":
            await r().set(f"filters_off:{chat_id}", "1")
        elif text == "تفعيل الردود":
            await r().delete(f"filters_off:{chat_id}")
        elif text == "تعطيل ردود المطور":
            await r().set(f"dev_filters_off:{chat_id}", "1")
        elif text == "تفعيل ردود المطور":
            await r().delete(f"dev_filters_off:{chat_id}")
        elif text == "تعطيل ردود الاعضاء":
            await r().set(f"member_filters_off:{chat_id}", "1")
        elif text == "تفعيل ردود الاعضاء":
            await r().delete(f"member_filters_off:{chat_id}")
        await reply_official(update, f"[k] تم: {text}\n[k]")
        return True
    return False
