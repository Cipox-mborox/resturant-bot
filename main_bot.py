import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, Filters
import json
from datetime import datetime

# Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Admin IDs (GANTI DENGAN ID TELEGRAM ANDA)
ADMIN_IDS = [7521156999]  # Ganti dengan ID Anda

# Load existing code from bot.py and admin_bot.py here...
# (Gabungkan semua fungsi dari kedua file)

def main():
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    updater = Updater(BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    
    # Customer handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("menu", show_menu))
    dispatcher.add_handler(CommandHandler("order", show_categories))
    dispatcher.add_handler(CommandHandler("status", order_status))
    dispatcher.add_handler(CommandHandler("help", help_command))
    
    # Admin handlers
    dispatcher.add_handler(CommandHandler("admin", admin_start))
    
    # Common handlers
    dispatcher.add_handler(CallbackQueryHandler(button_handler))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    logger.info("🤖 Restaurant Bot + Admin is running...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()