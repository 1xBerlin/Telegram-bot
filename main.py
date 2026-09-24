import os
import logging
import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = 7983129953:AAEFAohuecThFwm94hkUjVO2jZfMba-Qpww

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 أهلاً بك! أرسل لي رابط الفيديو من أي منصة وسأقوم بتحميله أو استخراج الصوت منه.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        await update.message.reply_text("❌ يرجى إرسال رابط صحيح!")
        return

    keyboard = [
        [
            InlineKeyboardButton("🎬 فيديو بأعلى دقة", callback_data=f"vid_best|{url}"),
            InlineKeyboardButton("🎵 استخراج الصوت (MP3)", callback_data=f"audio|{url}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("اختر الخيار المطلوب:", reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action, url = query.data.split("|", 1)
    await query.edit_message_text("⏳ جاري التحميل... يرجى الانتظار")

    file_prefix = f"dl_{query.from_user.id}"
    ydl_opts = {
        'outtmpl': f'{file_prefix}.%(ext)s',
        'quiet': True,
        'max_filesize': 50 * 1024 * 1024,
    }

    if action == "vid_best":
        ydl_opts['format'] = 'best'
    elif action == "audio":
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if action == "audio":
                filename = os.path.splitext(filename)[0] + ".mp3"

        if action == "audio":
            with open(filename, 'rb') as f:
                await context.bot.send_audio(chat_id=query.message.chat_id, audio=f, caption="🎵 تم استخراج الصوت")
        else:
            with open(filename, 'rb') as f:
                await context.bot.send_video(chat_id=query.message.chat_id, video=f, caption="🎬 تم تحميل الفيديو")

        if os.path.exists(filename):
            os.remove(filename)
    except Exception as e:
        await context.bot.send_message(chat_id=query.message.chat_id, text=f"❌ حدث خطأ: {str(e)}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_click))
    app.run_polling()
