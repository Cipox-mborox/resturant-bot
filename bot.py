import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    
    keyboard = [
        [InlineKeyboardButton("📋 Lihat Menu", callback_data="view_menu")],
        [InlineKeyboardButton("🛒 Pesan Sekarang", callback_data="start_order")],
        [InlineKeyboardButton("📞 Hubungi Kami", callback_data="contact")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = f"""
🍽️ **Selamat Datang di Restoran Kami!** 🍽️

Halo {user.first_name}! 
Siap memesan makanan lezat hari ini?

**Perintah tersedia:**
/menu - Lihat menu lengkap
/order - Buat pesanan baru  
/help - Bantuan pemesanan
    """
    
    update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

def menu(update: Update, context: CallbackContext):
    menu_text = """
🍽️ **MENU RESTORAN KAMI** 🍽️

**🍛 MAKANAN:**
• Nasi Goreng Spesial - Rp 25,000
• Mie Ayam Bakso - Rp 20,000
• Ayam Geprek - Rp 18,000

**🥤 MINUMAN:**
• Es Teh Manis - Rp 8,000
• Jus Alpukat - Rp 15,000
• Kopi Latte - Rp 12,000

**🍰 DESSERT:**
• Es Krim Vanilla - Rp 12,000
• Pudding Coklat - Rp 10,000
    """
    
    keyboard = [
        [InlineKeyboardButton("🛒 Pesan Sekarang", callback_data="start_order")],
        [InlineKeyboardButton("📞 Tanya Menu", callback_data="ask_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        update.callback_query.edit_message_text(menu_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        update.message.reply_text(menu_text, reply_markup=reply_markup, parse_mode='Markdown')

def order(update: Update, context: CallbackContext):
    order_text = """
🛒 **FITUR PEMESANAN**

Untuk pemesanan, silakan hubungi:
📱 WhatsApp: +62 812-3456-7890

Atau datang langsung ke restoran kami!

*Fitur online ordering sedang dalam pengembangan.*
    """
    
    if update.callback_query:
        update.callback_query.edit_message_text(order_text, parse_mode='Markdown')
    else:
        update.message.reply_text(order_text, parse_mode='Markdown')

def help_command(update: Update, context: CallbackContext):
    help_text = """
🆘 **BANTUAN**

**Cara Pesan:**
1. Lihat menu dengan /menu
2. Hubungi kami untuk pesan
3. Antar atau take away

**Info:**
• Buka: 09:00 - 22:00 WIB
• Area: Jakarta & Sekitarnya
• Min. pesanan: Rp 25,000

**Kontak:**
📱 WhatsApp: +62 812-3456-7890
📍 Lokasi: Jl. Restoran No. 123
    """
    update.message.reply_text(help_text, parse_mode='Markdown')

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    if query.data == "view_menu":
        menu(update, context)
    elif query.data == "start_order":
        order(update, context)
    elif query.data == "contact":
        query.edit_message_text(
            "📞 **HUBUNGI KAMI**\n\n"
            "📍 Alamat: Jl. Restoran No. 123, Jakarta\n"
            "📱 WhatsApp: +62 812-3456-7890\n"
            "🕒 Buka: 09:00 - 22:00 WIB\n\n"
            "*Free delivery untuk order > Rp 50,000*",
            parse_mode='Markdown'
        )
    elif query.data == "ask_menu":
        query.edit_message_text("Silakan hubungi kami untuk pertanyaan menu: +62 812-3456-7890")

def main():
    """Main function"""
    # Get token from environment
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not found in environment variables")
        return
    
    logger.info("🚀 Starting Restaurant Bot...")
    
    try:
        # Create updater and dispatcher
        updater = Updater(BOT_TOKEN, use_context=True)
        dispatcher = updater.dispatcher
        
        # Add handlers
        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(CommandHandler("menu", menu))
        dispatcher.add_handler(CommandHandler("order", order))
        dispatcher.add_handler(CommandHandler("help", help_command))
        dispatcher.add_handler(CallbackQueryHandler(button_handler))
        
        # Start the bot
        logger.info("🤖 Bot is now running with polling...")
        updater.start_polling()
        updater.idle()
        
    except Exception as e:
        logger.error(f"❌ Error starting bot: {e}")

if __name__ == '__main__':
    main()