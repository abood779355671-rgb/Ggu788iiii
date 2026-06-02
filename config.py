"""
الإعدادات العامة للبوت
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── الأساسيات ──────────────────────────────────────────
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
DEVP_ID = int(os.getenv("DEVP_ID", "0") or "0")  # صاحب البوت الأساسي
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
DEV_GROUP_ID = os.getenv("DEV_GROUP_ID", "")

# ── القيم الافتراضية القابلة للتغيير من لوحة المطور ──────
DEFAULT_BOT_NAME = "رعد"          # اسم البوت (prefix)
DEFAULT_BOT_KEY = "☆"             # رمز السورس BotKey
DEFAULT_SOURCE_CHANNEL = ""        # قناة السورس
DEFAULT_SOURCE_LINK = ""           # رابط السورس

# مفاتيح Redis لإعدادات المطور العامة
K_BOT_NAME = "cfg:botname"
K_BOT_KEY = "cfg:botkey"
K_SOURCE_CHANNEL = "cfg:source_channel"
K_SOURCE_LINK = "cfg:source_link"
K_DEV_GROUP = "cfg:dev_group"
K_DEVP = "cfg:devp"                 # المطور الأساسي (قابل للتغيير)
K_SERVICE_ENABLED = "cfg:service"   # البوت الخدمي مفعّل عام
K_DOWNLOAD_ENABLED = "cfg:download" # خدمة التحميل واليوتيوب
