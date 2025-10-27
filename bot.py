import logging
import os
import google.generativeai as genai
import threading
from flask import Flask
from dotenv import load_dotenv

# *** חשוב: זו הגרסה הישנה של הייבוא שתואמת לספרייה 13.15 ***
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

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
model = genai.GenerativeModel('gemini-1.5-flash')

# --- שרת אינטרנט פשוט ---
app = Flask(__name__)
@app.route('/')
def home():
    return "Bot is alive!", 200

def run_flask():
  port = int(os.environ.get('PORT', 8080))
  app.run(host='0.0.0.0', port=port)

# ---------------------------------

def start(update, context):
    update.message.reply_text('שלום! אני בוט המחובר ל-Gemini. שלחו לי הודעה ואענה.')

def handle_message(update, context):
    if 'chat_session' not in context.user_data:
        context.user_data['chat_session'] = model.start_chat(history=[])
    
    chat = context.user_data['chat_session']
    try:
        response = chat.send_message(update.message.text)
        update.message.reply_text(response.text)
    except Exception as e:
        logger.error(f"Error from Gemini: {e}")
        update.message.reply_text("מצטער, הייתה שגיאה בעיבוד הבקשה.")

def main_bot():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler("start", start))
    
    # *** חשוב: זו הגרסה הישנה של הפילטרים שתואמת לספרייה 13.15 ***
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    logger.info("Bot is polling...")
    updater.start_polling()

if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    
    main_bot()
