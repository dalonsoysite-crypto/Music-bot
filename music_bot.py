import logging, os, asyncio
from urllib.parse import urlparse
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
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

async def download_audio(url):
    opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{DOWNLOAD_DIR}/%(title)s.%(ext)s",
        "postprocessors": [{"key":"FFmpegExtractAudio","preferredcodec":"mp3","preferredquality":"192"}],
        "quiet": True, "noplaylist": True,
        "max_filesize": 48*1024*1024,
    }
    try:
        loop = asyncio.get_event_loop()
        def _dl():
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get("title","audio")
                path = os.path.splitext(ydl.prepare_filename(info))[0]+".mp3"
                return path, title
        return await loop.run_in_executor(None, _dl)
    except Exception as e:
        logger.error(e); return None, None

async def start(update, context):
    await update.message.reply_text("🎵 Musiqa linkini yuboring!")

async def handle(update, context):
    text = update.message.text.strip()
    if not is_url(text):
        await update.message.reply_text("❌ To'g'ri link yuboring!"); return
    msg = await update.message.reply_text("⏳ Yuklanmoqda...")
    path, title = await download_audio(text)
    if not path or not os.path.exists(path):
        await msg.edit_text("❌ Yuklab bo'lmadi!"); return
    try:
        await msg.edit_text(f"📤 {title}")
        with open(path,"rb") as f:
            await update.message.reply_audio(audio=f, title=title)
        await msg.delete()
    except:
        await msg.edit_text("❌ Xatolik!")
    finally:
        os.path.exists(path) and os.remove(path)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    app.run_polling()

if __name__ == "__main__":
    main()
