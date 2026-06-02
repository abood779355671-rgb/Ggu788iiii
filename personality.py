"""
§1 — الهوية والشخصية: الردود العاطفية العشوائية.
"""
import random

LOVE = ["يلبيييه", "اكثر", "يعمري", "اعشقك", "بدينا كذب", "احلى من يحبني",
        "يحظي والله", "يروحي", "اموت فيك"]

HATE = ["ابركها من ساعة", "احبك", "اكثر", "ترا ازعجتنا", "انقلع", "طيب",
        "مو اكثر مني", "وبعدين؟", "جت من الله", "توكل بس"]

SWEAR = ["عييييييب", "زق بوجهك", "يا قليل التربيه", "بقص لسانك", "حاضر", "ياخي عيب"]

NAME_CALL = ["نعم", "هلا والله", "امرني", "حياك", "تامر امر", "وش تبي؟",
             "اي نعم", "موجوده", "قول"]


def emotional_reply(text: str) -> str | None:
    """يرجّع رداً عاطفياً عشوائياً حسب النص، أو None لو ما فيه تطابق."""
    t = text.strip()

    if "احبك" in t or "أحبك" in t:
        return random.choice(LOVE)
    if "اكرهك" in t or "أكرهك" in t:
        return random.choice(HATE)
    if "كليزق" in t or "كلزق" in t:
        return random.choice(SWEAR)
    return None


def name_reply() -> str:
    return random.choice(NAME_CALL)
