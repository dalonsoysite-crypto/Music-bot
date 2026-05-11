import logging, os, asyncio, re
from urllib.parse import urlparse
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
import yt_dlp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TOKEN")
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def is_url(text):
    try:
        r = urlparse(text)
        return r.scheme in ("http","https") and bool(r.netloc)
    except:
        return False

def extract_url(text):
    urls = re.findall(r'https?://[^\s]+', text)
    return urls[0] if urls else None

async def download_audio(url):
    opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{DOWNLOAD_DIR}/%(title)s.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "128",
        }],
        "quiet": True,
        "noplaylist": True,
        "max_filesize": 45*1024*1024,
        "socket_timeout": 30,
        "retries": 3,
    }
    try:
        loop = asyncio.get_event_loop()
        def _dl():
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get("title", "audio")
                path = os.path.splitext(ydl.prepare_filename(info))[0] + ".mp3"
                return path, title
        return await loop.run_in_executor(None, _dl)
    except Exception as e:
        logger.error(e)
        return None, None

async def start(update, context):
    await update.message.reply_text(
        "🎵 *Musiqa Yuklovchi Bot*\n\n"
        "Menga istalgan saytdan musiqa linkini yuboring!\n\n"
        "✅ YouTube\n"
        "✅ SoundCloud\n"
        "✅ TikTok\n"
        "✅ VK\n"
        "✅ 1000+ boshqa saytlar\n\n"
        "📌 Faqat link yuboring!",
        parse_mode="Markdown"
    )

async def handle(update, context):
    text = update.message.text.strip()
    url = extract_url(text) if not is_url(text) else text
    if not url:
        await update.message.reply_text(
            "❌ Link topilmadi!\n"
            "Misol: https://youtube.com/watch?v=..."
        )
        return
    msg = await update.message.reply_text("⏳ Yuklanmoqda... Sabr qiling!")
    path, title = await download_audio(url)
    if not path or not os.path.exists(path):
        await msg.edit_text(
            "❌ Yuklab bo'lmadi!\n"
            "• Link noto'g'ri bo'lishi mumkin\n"
            "• Yoki fayl 45MB dan katta\n"
            "• Yoki bu sayt qo'llab-quvvatlanmaydi"
        )
        return
    try:
        await msg.edit_text(f"📤 Yuborilmoqda: *{title}*", parse_mode="Markdown")
        with open(path, "rb") as f:
            await update.message.reply_audio(
                audio=f,
                title=title,
                caption=f"🎵 {title}\n\n📸 Instagram: @toshbekov_f"
            )
        await msg.delete()
    except Exception as e:
        logger.error(e)
        await msg.edit_text("❌ Yuborishda xatolik!")
    finally:
        if os.path.exists(path):
            os.remove(path)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    logger.info("Bot ishga tushdi!")
    app.run_polling()

if __name__ == "__main__":
    main()
