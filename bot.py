import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler
import requests
import json

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class RestaurantBot:
    def __init__(self):
        self.token = os.getenv('BOT_TOKEN')
        self.google_script_url = os.getenv('GOOGLE_SCRIPT_URL')
        self.port = int(os.getenv('PORT', 8443))
        
        # Initialize updater
        self.updater = Updater(self.token, use_context=True)
        self.dispatcher = self.updater.dispatcher
        
        self.setup_handlers()
        self.user_sessions = {}

    def setup_handlers(self):
        """Setup command handlers"""
        self.dispatcher.add_handler(CommandHandler("start", self.start))
        self.dispatcher.add_handler(CommandHandler("menu", self.menu))
        self.dispatcher.add_handler(CommandHandler("order", self.order))
        self.dispatcher.add_handler(CommandHandler("help", self.help))
        
        self.dispatcher.add_handler(CallbackQueryHandler(self.button_handler))

    def call_google_script(self, data):
        """Call Google Apps Script webapp"""
        try:
            response = requests.post(self.google_script_url, json=data, timeout=10)
            return response.json()
        except Exception as e:
            logger.error(f"Error calling Google Script: {e}")
            return None

    def start(self, update: Update, context: CallbackContext):
        """Send welcome message"""
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

*Pesan melalui bot, makanan langsung sampai!*
        """
        
        update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

    def menu(self, update: Update, context: CallbackContext):
        """Show restaurant menu"""
        # Sample menu data - bisa diganti dengan Google Apps Script
        menu_text = """
🍽️ **MENU RESTORAN KAMI** 🍽️

**🍛 MAKANAN:**
• Nasi Goreng Spesial - Rp 25,000
• Mie Ayam Bakso - Rp 20,000
• Ayam Geprek - Rp 18,000
• Capcay Kuah - Rp 22,000

**🥤 MINUMAN:**
• Es Teh Manis - Rp 8,000
• Jus Alpukat - Rp 15,000
• Kopi Latte - Rp 12,000
• Air Mineral - Rp 5,000

**🍰 DESSERT:**
• Es Krim Vanilla - Rp 12,000
• Pudding Coklat - Rp 10,000
• Fruit Salad - Rp 15,000
        """
        
        keyboard = [
            [InlineKeyboardButton("🛒 Pesan Sekarang", callback_data="start_order")],
            [InlineKeyboardButton("📞 Tanya Menu", callback_data="ask_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        update.message.reply_text(menu_text, reply_markup=reply_markup, parse_mode='Markdown')

    def order(self, update: Update, context: CallbackContext):
        """Start order process"""
        user_id = update.effective_user.id
        self.user_sessions[user_id] = {'step': 'waiting_name'}
        
        update.message.reply_text(
            "🛒 **MEMULAI PEMESANAN**\n\n"
            "Silakan ketik nama lengkap Anda:"
        )

    def help(self, update: Update, context: CallbackContext):
        """Show help message"""
        help_text = """
🆘 **BANTUAN PEMESANAN**

**Cara Pesan:**
1. Ketik /menu untuk lihat menu
2. Ketik /order untuk mulai pesan
3. Ikuti instruksi bot

**Metode Bayar:**
• Transfer Bank (BCA, BRI, Mandiri)
• Tunai (COD - Cash On Delivery)

**Info Layanan:**
• Area pengiriman: Jakarta & Sekitarnya
• Min. pesanan: Rp 25,000
• Estimasi: 30-45 menit

**Problem?** Hubungi: @admin_restaurant
        """
        
        update.message.reply_text(help_text, parse_mode='Markdown')

    def button_handler(self, update: Update, context: CallbackContext):
        """Handle button callbacks"""
        query = update.callback_query
        query.answer()
        
        data = query.data
        
        if data == "view_menu":
            self.menu(query, context)
        elif data == "start_order":
            self.order(query, context)
        elif data == "contact":
            query.edit_message_text(
                "📞 **HUBUNGI KAMI**\n\n"
                "📍 Alamat: Jl. Restoran No. 123, Jakarta\n"
                "📱 WhatsApp: +62 812-3456-7890\n"
                "🕒 Buka: 09:00 - 22:00 WIB\n"
                "🔗 Instagram: @restoran_kita\n\n"
                "*Free delivery untuk order > Rp 50,000*",
                parse_mode='Markdown'
            )
        elif data == "ask_menu":
            query.edit_message_text(
                "❓ **PERTANYAAN MENU**\n\n"
                "Ada pertanyaan tentang menu?\n"
                "Silakan chat langsung ke admin:\n"
                "@admin_restaurant"
            )

    def run_webhook(self):
        """Run with webhook for production"""
        webhook_url = os.getenv('RAILWAY_STATIC_URL')
        if webhook_url:
            self.updater.start_webhook(
                listen="0.0.0.0",
                port=self.port,
                url_path=self.token,
                webhook_url=f"{webhook_url}/{self.token}"
            )
            logger.info("🤖 Bot running with webhook...")
        else:
            self.run_polling()

    def run_polling(self):
        """Run with polling for development"""
        logger.info("🤖 Bot running with polling...")
        self.updater.start_polling()
        self.updater.idle()

def main():
    """Main function to start the bot"""
    # Check required environment variables
    required_vars = ['BOT_TOKEN']
    for var in required_vars:
        if not os.getenv(var):
            logger.error(f"❌ Missing required environment variable: {var}")
            return
    
    bot = RestaurantBot()
    
    # Check if running on Railway
    if os.getenv('RAILWAY_ENVIRONMENT'):
        bot.run_webhook()
    else:
        bot.run_polling()

if __name__ == '__main__':
    main()