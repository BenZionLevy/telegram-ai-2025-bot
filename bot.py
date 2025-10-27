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
    """שולח הודעת פתיחה."""
    await update.message.reply_text('שלום! אני בוט המחובר ל-Gemini. שלחו לי הודעה ואענה.')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """מטפל בהודעות טקסט מהמשתמש."""
    if 'chat_session' not in context.user_data:
        context.user_data['chat_session'] = model.start_chat(history=[])
    
    # תיקון קריטי: מוציאים את המשתנה מחוץ ל-if כדי שיעבוד גם בהודעות הבאות
    chat = context.user_data['chat_session']
    
    try:
        response = await asyncio.to_thread(chat.send_message, update.message.text)
        await update.message.reply_text(response.text)
    except Exception as e:
        logger.error(f"Error from Gemini: {e}")
        await update.message.reply_text("מצטער, הייתה שגיאה בעיבוד הבקשה.")

def main():
    """הפונקציה הראשית שמפעילה את הכל."""
    
    # 1. הרצת שרת האינטרנט בתהליך נפרד (thread)
    # daemon=True גורם לתהליך להיסגר כשהתוכנית הראשית נסגרת
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # 2. בנייה והרצה של הבוט
    logger.info("Starting bot...")
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # הוספת המטפלים (handlers)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # הרצת הבוט עד שהתהליך יופסק
    application.run_polling()

if __name__ == '__main__':
    main()

