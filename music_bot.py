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
INSTAGRAM = "@toshbekov_f"

VIDEO_SITES = ["instagram.com", "tiktok.com", "vm.tiktok.com", "vt.tiktok.com"]

def is_url(text):
    try:
        r = urlparse(text)
        return r.scheme in ("http","https") and bool(r.netloc)
    except:
        return False

def extract_url(text):
    urls = re.findall(r'https?://[^\s]+', text)
    return urls[0] if urls else None

def is_video_site(url):
    return any(site in url.lower() for site in VIDEO_SITES)

async def download_audio(url):
    opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{DOWNLOAD_DIR}/%(title)s.%(ext)s",
        "postprocessors": [{"key":"FFmpegExtractAudio","preferredcodec":"mp3","preferredquality":"128"}],
        "quiet": True, "noplaylist": True,
        "max_filesize": 45*1024*1024,
        "socket_timeout": 30, "retries": 3,
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

async def download_video(url):
    opts = {
        "format": "best[filesize<45M]/best",
        "outtmpl": f"{DOWNLOAD_DIR}/%(title)s.%(ext)s",
        "quiet": True, "noplaylist": True,
        "max_filesize": 45*1024*1024,
        "socket_timeout": 30, "retries": 3,
    }
    try:
        loop = asyncio.get_event_loop()
        def _dl():
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get("title","video")
                path = ydl.prepare_filename(info)
                return path, title
        return await loop.run_in_executor(None, _dl)
    except Exception as e:
        logger.error(e); return None, None

async def start(update, context):
    await update.message.reply_text(
        "🎵 *Media Yuklovchi Bot*\n\n"
        "Link yuboring — bot o'zi tanlaydi!\n\n"
        "🎬 Instagram / TikTok → Video\n"
        "🎵 YouTube / SoundCloud → MP3\n\n"
        "✅ 1000+ sayt qo'llab-quvvatlanadi\n\n"
        "📸 Instagram: @toshbekov_f",
        parse_mode="Markdown"
    )

async def handle(update, context):
    text = update.message.text.strip()
    url = extract_url(text) if not is_url(text) else text
    if not url:
        await update.message.reply_text(
            "❌ Link topilmadi!\n"
            "Misol: https://youtube.com/..."
        )
        return

    if is_video_site(url):
        msg = await update.message.reply_text("⏳ Video yuklanmoqda...")
        path, title = await download_video(url)
        if not path or not os.path.exists(path):
            await msg.edit_text("❌ Yuklab bo'lmadi!\n• Video 45MB dan katta bo'lishi mumkin")
            return
        try:
            await msg.edit_text(f"📤 {title}")
            with open(path,"rb") as f:
                await update.message.reply_video(
                    video=f,
                    caption=f"🎬 {title}\n\n📸 Instagram: {INSTAGRAM}"
                )
            await msg.delete()
        except Exception as e:
            logger.error(e)
            await msg.edit_text("❌ Xatolik!")
        finally:
            if os.path.exists(path): os.remove(path)
    else:
        msg = await update.message.reply_text("⏳ MP3 yuklanmoqda...")
        path, title = await download_audio(url)
        if not path or not os.path.exists(path):
            await msg.edit_text("❌ Yuklab bo'lmadi!\n• Link noto'g'ri bo'lishi mumkin\n• Yoki fayl 45MB dan katta")
            return
        try:
            await msg.edit_text(f"📤 {title}")
            with open(path,"rb") as f:
                await update.message.reply_audio(
                    audio=f,
                    title=title,
                    caption=f"🎵 {title}\n\n📸 Instagram: {INSTAGRAM}"
                )
            await msg.delete()
        except Exception as e:
            logger.error(e)
            await msg.edit_text("❌ Xatolik!")
        finally:
            if os.path.exists(path): os.remove(path)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    logger.info("Bot ishga tushdi!")
    app.run_polling()

if __name__ == "__main__":
    main()
