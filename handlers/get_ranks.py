"""
§8 — عرض الرتب والقوائم + §4 تخصيص أسماء الرتب.
"""
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

import ranks
import state
from utils import mention_id, reply_official


async def _format_list(context, chat_id, user_ids, title) -> str:
    if not user_ids:
        return f"[k] {title}\n[k] لا يوجد"
    lines = [f"[k] {title}\n"]
    for i, uid in enumerate(user_ids, 1):
        try:
            cm = await context.bot.get_chat_member(chat_id, uid)
            name = cm.user.full_name
        except Exception:
            name = str(uid)
        lines.append(f"{i} ⌯ {mention_id(uid, name)}")
    return "\n".join(lines)


async def cmd_list_ranks(update: Update, context: ContextTypes.DEFAULT_TYPE,
                         text: str, rank: int) -> bool:
    chat_id = update.effective_chat.id

    mapping = {
        "الادمن": (ranks.ADMIN, "قائمة الادمن"),
        "قائمة الادمن": (ranks.ADMIN, "قائمة الادمن"),
        "المدراء": (ranks.MOD, "قائمة المدراء"),
        "الملاك": (ranks.OWNER, "قائمة الملاك"),
        "المميزين": (ranks.PRE, "قائمة المميزين"),
    }
    if text in mapping:
        level, title = mapping[text]
        uids = await ranks.list_rank(chat_id, level)
        msg = await _format_list(context, chat_id, uids, title)
        await reply_official(update, msg)
        return True

    if text == "قائمة الكتم":
        uids = await state.list_muted_local(chat_id)
        msg = await _format_list(context, chat_id, uids, "قائمة الكتم")
        await reply_official(update, msg)
        return True

    if text == "قائمة الكتم العام":
        uids = await state.list_muted_global()
        msg = await _format_list(context, chat_id, uids, "قائمة الكتم العام")
        await reply_official(update, msg)
        return True

    if text == "قائمة الحظر العام":
        uids = await state.list_gbanned()
        msg = await _format_list(context, chat_id, uids, "قائمة الحظر العام")
        await reply_official(update, msg)
        return True

    return False


# ── تخصيص أسماء الرتب (§4) ──────────────────────────────
SET_NAME_MAP = [
    ("تعيين اسم المالك الاساسي", ranks.GOWNER),
    ("تعيين اسم المالك", ranks.OWNER),
    ("تعيين اسم المدير", ranks.MOD),
    ("تعيين اسم الادمن", ranks.ADMIN),
    ("تعيين اسم المميز", ranks.PRE),
    ("تعيين اسم العضو", ranks.MEMBER),
]

CLEAR_NAME_MAP = [
    ("مسح اسم المالك الاساسي", ranks.GOWNER),
    ("مسح اسم المالك", ranks.OWNER),
    ("مسح اسم المدير", ranks.MOD),
    ("مسح اسم الادمن", ranks.ADMIN),
    ("مسح اسم المميز", ranks.PRE),
    ("مسح اسم العضو", ranks.MEMBER),
]


async def cmd_custom_rank(update: Update, context: ContextTypes.DEFAULT_TYPE,
                          text: str, rank: int) -> bool:
    chat_id = update.effective_chat.id

    for prefix, level in SET_NAME_MAP:
        if text.startswith(prefix):
            if rank < ranks.OWNER:
                await reply_official(update, "[k] هذا الامر يخص ( المالك وفوق ) بس")
                return True
            name = text[len(prefix):].strip()
            if not name:
                await reply_official(update, "[k] اكتب الاسم بعد الامر")
                return True
            await ranks.set_rank_name(chat_id, level, name)
            await reply_official(update, f"[k] غيرت اسم الرتبه الى: {name}\n[k]")
            return True

    for prefix, level in CLEAR_NAME_MAP:
        if text.startswith(prefix):
            if rank < ranks.OWNER:
                await reply_official(update, "[k] هذا الامر يخص ( المالك وفوق ) بس")
                return True
            await ranks.clear_rank_name(chat_id, level)
            default = ranks.DEFAULT_NAMES.get(level, "عضو")
            await reply_official(update, f"[k] رجعت الاسم الافتراضي: {default}\n[k]")
            return True

    return False
