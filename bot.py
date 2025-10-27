import logging
import os
import google.generativeai as genai
import threading
from flask import Flask
from dotenv import load_dotenv
import asyncio

# ייבואים מעודכנים לגרסה 20.x
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- טעינת המשתנים הסודיים ---
load_dotenv()
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# --- הגדרות לוגינג ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- אתחול Gemini API ---
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# --- שרת אינטרנט פשוט כדי שהבוט יישאר חי ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is alive!", 200

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

# --- פונקציות הבוט (מעודכנות עם async/await) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('שלום! אני בוט המחובר ל-Gemini. שלחו לי הודעה ואענה.')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # !!! הוספנו את שורת הבדיקה הזו !!!
    logger.info(f"Received a message! Attempting to process for user {update.effective_chat.id}")
    
    if 'chat_session' not in context.user_data:
        context.user_data['chat_session'] = model.start_chat(history=[])
    
    chat = context.user_data['chat_session']
    
    try:
        response = await asyncio.to_thread(chat.send_message, update.message.text)
        await update.message.reply_text(response.text)
    except Exception as e:
        logger.error(f"CRITICAL ERROR from Gemini or during processing: {e}")
        await update.message.reply_text("מצטער, הייתה שגיאה קריטית בעיבוד הבקשה.")

def main():
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    logger.info("Starting bot with modern library...")
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    application.run_polling()

if __name__ == '__main__':
    main()
