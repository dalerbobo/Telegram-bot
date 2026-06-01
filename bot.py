import logging
import asyncio
import os

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile

import yt_dlp

TOKEN = "8797976234:AAFTEKe8x5uA_fq3KIxlVUL9Bxu8gzfr3XQ"

bot = Bot(token=TOKEN)
dp = Dispatcher()
logging.getLogger("aiogram").setLevel(logging.CRITICAL)
logging.getLogger("yt_dlp").setLevel(logging.CRITICAL)
logging.basicConfig(level=logging.ERROR)

# ---------------- START ----------------


@dp.message(Command("start"))
async def start(message: types.Message):

    text = (
        "🎬 Media Link Bot\n\n"
        "Отправь ссылку YouTube.\n\n"
        "Доступно:\n"
        "• Видео MP4\n"
        "• Аудио MP3"
    )

    await message.answer(text)


# ---------------- HANDLE LINKS ----------------


@dp.message()
async def handle_link(message: types.Message):

    url = message.text
    print("LINK RECEIVED:", url) 
    ydl_opts = {
        "quiet": False,
        "no_warnings": False,
    }

    print("GETTING VIDEO INFO...")
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        
        print("VIDEO INFO RECEIVED")
    except Exception as e:
        print("YTDLP ERROR:", e)
        await message.answer(f"Ошибка: {e}")
        return
        title = info.get("title", "Unknown")
        duration = info.get("duration", 0)
        views = info.get("view_count", 0)
        thumbnail = info.get("thumbnail")
        minutes = duration // 60
        seconds = duration % 60
        
        if "youtube.com" in url or "youtu.be" in url:
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="🎧 MP3", callback_data=f"audio|{url}")],
                    [InlineKeyboardButton(text="🎬 144p", callback_data=f"144|{url}")],
                    [InlineKeyboardButton(text="🎬 240p", callback_data=f"240|{url}")],
                    [InlineKeyboardButton(text="🎬 360p", callback_data=f"360|{url}")],
                    [InlineKeyboardButton(text="🎬 480p", callback_data=f"480|{url}")],
                    [InlineKeyboardButton(text="🎬 720p", callback_data=f"720|{url}")],
                    [InlineKeyboardButton(text="🎬 1080p", callback_data=f"1080|{url}")],
                ]
            )
            caption = (
                f"🎬 {title}\n\n"
                f"👀 Просмотры: {views:,}\n"
                f"⏱ Длительность: {minutes}:{seconds:02d}\n\n"
                f"Выбери качество:"
            )
            await message.answer_photo(
                photo=thumbnail, caption=caption, reply_markup=keyboard\
            )
        else:
            await message.answer("❌ Поддерживается только YouTube")


# ---------------- CALLBACKS ----------------


@dp.callback_query()
async def callbacks(callback: types.CallbackQuery):

    await callback.answer("⏳ Processing...")

    action, url = callback.data.split("|", 1)

    loading = await callback.message.answer("⏳ Downloading...")

    try:

        # ---------------- VIDEO ----------------

        if action.isdigit():

            if os.path.exists("video.mp4"):
                os.remove("video.mp4")

            quality = action

            ydl_opts = {
                "format": f"bestvideo[height<={quality}]+bestaudio/best[height<={quality}]",
                "outtmpl": "%(title)s.%(ext)s",
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
                "continuedl": False,
                "nopart": True,
                "retries": 10,
                "fragment_retries": 10,
                "extractor_args": {"youtube": {"player_client": ["android"]}},
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

            await asyncio.sleep(2)

            if not os.path.exists(filename):
                await loading.delete()
                await callback.message.answer("❌ Видео не найдено")
                return

            print("VIDEO FILE:", filename)

            video = FSInputFile(filename)

            await bot.send_video(
                chat_id=callback.message.chat.id,
                video=video,
                caption="🎬 Video downloaded",
            )

            await loading.delete()

            os.remove(filename)

        # ---------------- AUDIO ----------------

        elif action == "audio":

            if os.path.exists("audio.mp3"):
                os.remove("audio.mp3")

            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": "%(title)s.%(ext)s",
                "quiet": True,
                "noplaylist": True,
                "retries": 10,
                "extractor_args": {"youtube": {"player_client": ["android"]}},
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

            title = info["title"]

            audio_file = None

            for f in os.listdir():
                if f.endswith(".mp3"):
                    audio_file = f
                    break

            print("TITLE:", title)

            for f in os.listdir():
                print("FILE:", f)

            await asyncio.sleep(2)

            if audio_file is None:
                await loading.delete()
                await callback.message.answer("❌ Аудио не найдено")
                return
            audio = FSInputFile(audio_file)

            await bot.send_audio(
                chat_id=callback.message.chat.id,
                audio=audio,
                caption="🎧 Audio downloaded",
            )

            await loading.delete()

            os.remove(audio_file)

    except Exception as e:

        print(e)

        await loading.delete()

        await callback.message.answer("❌ Ошибка загрузки.\nПопробуй другое видео.")


# ---------------- MAIN ----------------


async def main():

    print("BOT STARTED")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
