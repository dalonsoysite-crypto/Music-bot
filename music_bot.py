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

async def download_photo(url):
    opts = {
        "format": "best",
        "outtmpl": f"{DOWNLOAD_DIR}/%(title)s.%(ext)s",
        "quiet": True, "noplaylist": True,
        "writethumbnail": True,
        "skip_download": True,
        "socket_timeout": 30,
    }
    try:
        loop = asyncio.get_event_loop()
        def _dl():
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get("title","photo")
                thumb = info.get("thumbnail","")
                return thumb, title
        return await loop.run_in_executor(None, _dl)
    except Exception as e:
        logger.error(e); return None, None

async def start(update, context):
    await update.message.reply_text(
        "🎵 *Media Yuklovchi Bot*\n\n"
        "Menga link yuboring va formatni tanlang!\n\n"
        "🎵 /mp3 — Musiqa\n"
        "🎬 /video — Qisqa video (max 45MB)\n"
        "📸 /foto — Foto\n\n"
        "✅ YouTube, TikTok, Instagram, VK va 1000+ sayt\n\n"
        "Misol: /mp3 https://youtube.com/...",
        parse_mode="Markdown"
    )

async def mp3_cmd(update, context):
    if not context.args:
        await update.message.reply_text("❌ Link yuboring!\nMisol: /mp3 https://youtube.com/...")
        return
    url = context.args[0]
    msg = await update.message.reply_text("⏳ MP3 yuklanmoqda...")
    path, title = await download_audio(url)
    if not path or not os.path.exists(path):
        await msg.edit_text("❌ Yuklab bo'lmadi!"); return
    try:
        await msg.edit_text(f"📤 {title}")
        with open(path,"rb") as f:
            await update.message.reply_audio(audio=f, title=title,
                caption=f"🎵 {title}\n\n📸 Instagram: {INSTAGRAM}")
        await msg.delete()
    except Exception as e:
        logger.error(e); await msg.edit_text("❌ Xatolik!")
    finally:
        if os.path.exists(path): os.remove(path)

async def video_cmd(update, context):
    if not context.args:
        await update.message.reply_text("❌ Link yuboring!\nMisol: /video https://youtube.com/...")
        return
    url = context.args[0]
    msg = await update.message.reply_text("⏳ Video yuklanmoqda...")
    path, title = await download_video(url)
    if not path or not os.path.exists(path):
        await msg.edit_text("❌ Yuklab bo'lmadi! Video 45MB dan katta bo'lishi mumkin."); return
    try:
        await msg.edit_text(f"📤 {title}")
        with open(path,"rb") as f:
            await update.message.reply_video(video=f,
                caption=f"🎬 {title}\n\n📸 Instagram: {INSTAGRAM}")
        await msg.delete()
    except Exception as e:
        logger.error(e); await msg.edit_text("❌ Xatolik!")
    finally:
        if os.path.exists(path): os.remove(path)

async def foto_cmd(update, context):
    if not context.args:
        await update.message.reply_text("❌ Link yuboring!\nMisol: /foto https://instagram.com/...")
        return
    url = context.args[0]
    msg = await update.message.reply_text("⏳ Foto yuklanmoqda...")
    thumb_url, title = await download_photo(url)
    if not thumb_url:
        await msg.edit_text("❌ Foto topilmadi!"); return
    try:
        await msg.edit_text(f"📤 {title}")
        await update.message.reply_photo(photo=thumb_url,
            caption=f"📸 {title}\n\n📸 Instagram: {INSTAGRAM}")
        await msg.delete()
    except Exception as e:
        logger.error(e); await msg.edit_text("❌ Xatolik!")

async def handle(update, context):
    text = update.message.text.strip()
    url = extract_url(text) if not is_url(text) else text
    if not url:
        await update.message.reply_text(
            "❌ Link topilmadi!\n\n"
            "🎵 /mp3 [link] — Musiqa\n"
            "🎬 /video [link] — Video\n"
            "📸 /foto [link] — Foto"
        ); return
    msg = await update.message.reply_text("⏳ Yuklanmoqda...")
    path, title = await download_audio(url)
    if not path or not os.path.exists(path):
        await msg.edit_text("❌ Yuklab bo'lmadi!"); return
    try:
        await msg.edit_text(f"📤 {title}")
        with open(path,"rb") as f:
            await update.message.reply_audio(audio=f, title=title,
                caption=f"🎵 {title}\n\n📸 Instagram: {INSTAGRAM}")
        await msg.delete()
    except Exception as e:
        logger.error(e); await msg.edit_text("❌ Xatolik!")
    finally:
        if os.path.exists(path): os.remove(path)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("mp3", mp3_cmd))
    app.add_handler(CommandHandler("video", video_cmd))
    app.add_handler(CommandHandler("foto", foto_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    logger.info("Bot ishga tushdi!")
    app.run_polling()

if __name__ == "__main__":
    main()
