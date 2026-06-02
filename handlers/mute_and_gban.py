"""
§6 — الكتم والحظر.
كل دالة ترجّع True لو عالجت الأمر.
"""
from telegram import Update
from telegram.ext import ContextTypes

import ranks
import state
from utils import resolve_target, reply_official, mention_id


async def _target_rank(chat_id: int, uid: int) -> int:
    return await ranks.get_rank(chat_id, uid)


# ── كتم محلي ────────────────────────────────────────────
async def cmd_mute(update: Update, context: ContextTypes.DEFAULT_TYPE,
                   text: str, rank: int) -> bool:
    chat_id = update.effective_chat.id
    issuer = update.effective_user.id
    is_reply = update.effective_message.reply_to_message is not None

    # الصلاحية: بالرد mod وفوق، باليوزر admin وفوق
    needed = ranks.MOD if is_reply else ranks.ADMIN
    if rank < needed:
        rn = await ranks.get_rank_name(chat_id, needed)
        await reply_official(update, f"[k] هذا الامر يخص ( {rn} وفوق ) بس")
        return True

    uid, name = await resolve_target(update, context, text)
    if not uid:
        await reply_official(update, "[k] رد على رسالة العضو او حط ايديه")
        return True

    if uid == issuer:
        await reply_official(update, "[k] شفيك تبي تنزل نفسك")
        return True

    target_rank = await _target_rank(chat_id, uid)
    if target_rank >= rank or target_rank >= ranks.PRE and target_rank >= rank:
        rn = await ranks.get_rank_name(chat_id, target_rank)
        await reply_official(update, f"[k] هييه مايمديك تكتم {rn} يورع!")
        return True
    if target_rank >= rank:
        await reply_official(update, "[k] مايمديك تكتم احد فوقك يورع!")
        return True

    if await state.is_muted_local(chat_id, uid):
        await reply_official(
            update, f"「 {mention_id(uid, name)} 」\n[k] مكتوم من قبل\n[k]")
        return True

    await state.mute_local(chat_id, uid)
    await reply_official(
        update, f"「 {mention_id(uid, name)} 」\n[k] كتمته\n[k]")
    return True


async def cmd_unmute(update: Update, context: ContextTypes.DEFAULT_TYPE,
                     text: str, rank: int) -> bool:
    chat_id = update.effective_chat.id
    is_reply = update.effective_message.reply_to_message is not None
    needed = ranks.ADMIN if is_reply else ranks.MOD
    if rank < needed:
        rn = await ranks.get_rank_name(chat_id, needed)
        await reply_official(update, f"[k] هذا الامر يخص ( {rn} وفوق ) بس")
        return True

    uid, name = await resolve_target(update, context, text)
    if not uid:
        await reply_official(update, "[k] رد على رسالة العضو او حط ايديه")
        return True

    await state.unmute_local(chat_id, uid)
    await reply_official(
        update, f"「 {mention_id(uid, name)} 」\n[k] فكيت كتمه\n[k]")
    return True


# ── كتم عام ─────────────────────────────────────────────
async def cmd_gmute(update: Update, context: ContextTypes.DEFAULT_TYPE,
                    text: str, rank: int) -> bool:
    chat_id = update.effective_chat.id
    if rank < ranks.DEV:
        rn = await ranks.get_rank_name(chat_id, ranks.DEV)
        await reply_official(update, f"[k] هذا الامر يخص ( {rn} وفوق ) بس")
        return True

    uid, name = await resolve_target(update, context, text)
    if not uid:
        await reply_official(update, "[k] رد على رسالة العضو او حط ايديه")
        return True

    await state.mute_global(uid)
    await reply_official(
        update, f"「 {mention_id(uid, name)} 」\n[k] كتمته عام\n[k]")
    return True


async def cmd_ungmute(update: Update, context: ContextTypes.DEFAULT_TYPE,
                      text: str, rank: int) -> bool:
    chat_id = update.effective_chat.id
    if rank < ranks.DEV:
        rn = await ranks.get_rank_name(chat_id, ranks.DEV)
        await reply_official(update, f"[k] هذا الامر يخص ( {rn} وفوق ) بس")
        return True

    uid, name = await resolve_target(update, context, text)
    if not uid:
        await reply_official(update, "[k] رد على رسالة العضو او حط ايديه")
        return True

    await state.unmute_global(uid)
    await reply_official(
        update, f"「 {mention_id(uid, name)} 」\n[k] فكيت كتمه العام\n[k]")
    return True


# ── الحظر العام ─────────────────────────────────────────
async def cmd_gban(update: Update, context: ContextTypes.DEFAULT_TYPE,
                   text: str, rank: int) -> bool:
    chat_id = update.effective_chat.id
    if rank < ranks.DEV:
        rn = await ranks.get_rank_name(chat_id, ranks.DEV)
        await reply_official(update, f"[k] هذا الامر يخص ( {rn} وفوق ) بس")
        return True

    uid, name = await resolve_target(update, context, text)
    if not uid:
        await reply_official(update, "[k] رد على رسالة العضو او حط ايديه")
        return True

    await state.gban(uid)
    try:
        await context.bot.ban_chat_member(chat_id, uid)
    except Exception:
        pass
    await reply_official(
        update, f"[k] الحمار「 {mention_id(uid, name)} 」\n[k] حظرته عام\n[k]")
    return True


async def cmd_ungban(update: Update, context: ContextTypes.DEFAULT_TYPE,
                     text: str, rank: int) -> bool:
    chat_id = update.effective_chat.id
    if rank < ranks.DEV:
        rn = await ranks.get_rank_name(chat_id, ranks.DEV)
        await reply_official(update, f"[k] هذا الامر يخص ( {rn} وفوق ) بس")
        return True

    uid, name = await resolve_target(update, context, text)
    if not uid:
        await reply_official(update, "[k] رد على رسالة العضو او حط ايديه")
        return True

    await state.ungban(uid)
    try:
        await context.bot.unban_chat_member(chat_id, uid, only_if_banned=True)
    except Exception:
        pass
    await reply_official(
        update, f"「 {mention_id(uid, name)} 」\n[k] فكيت حظره العام\n[k]")
    return True
