import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, Filters
# Tambah di imports
import json
from datetime import datetime

# Tambah constant
ORDERS_FILE = 'orders.json'

def load_orders():
    """Load orders from JSON file"""
    try:
        with open(ORDERS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_orders(orders):
    """Save orders to JSON file"""
    with open(ORDERS_FILE, 'w') as f:
        json.dump(orders, f, indent=2)

# Update fungsi create_order
def create_order(user_id, session):
    order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    orders = load_orders()
    
    orders[order_id] = {
        'user_id': user_id,
        'customer_name': session['customer_name'],
        'phone': session['phone'],
        'address': session['address'],
        'items': session['cart'].copy(),
        'total': sum(item['price'] for item in session['cart']),
        'status': 'baru',  # Status awal
        'timestamp': datetime.now().isoformat()
    }
    
    save_orders(orders)
    return order_id

# Update fungsi order_status untuk baca dari file
def order_status(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    orders = load_orders()
    
    # Find user's orders
    user_orders = []
    for order_id, order in orders.items():
        if order['user_id'] == user_id:
            user_orders.append((order_id, order))
    
    # ... (sisanya sama)

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# In-memory storage (nanti bisa diganti dengan database)
user_sessions = {}
orders = {}

# Menu database
MENU_ITEMS = {
    'makanan': [
        {'id': 'M001', 'name': 'Nasi Goreng Spesial', 'price': 25000, 'desc': 'Nasi goreng dengan ayam dan seafood'},
        {'id': 'M002', 'name': 'Mie Ayam Bakso', 'price': 20000, 'desc': 'Mie ayam dengan bakso urat'},
        {'id': 'M003', 'name': 'Ayam Geprek', 'price': 18000, 'desc': 'Ayam crispy dengan sambal bawang'},
    ],
    'minuman': [
        {'id': 'D001', 'name': 'Es Teh Manis', 'price': 8000, 'desc': 'Es teh dengan gula merah'},
        {'id': 'D002', 'name': 'Jus Alpukat', 'price': 15000, 'desc': 'Jus alpukat dengan susu dan es krim'},
        {'id': 'D003', 'name': 'Kopi Latte', 'price': 12000, 'desc': 'Kopi espresso dengan susu steamed'},
    ],
    'dessert': [
        {'id': 'S001', 'name': 'Es Krim Vanilla', 'price': 12000, 'desc': 'Es krim homemade vanilla'},
        {'id': 'S002', 'name': 'Pudding Coklat', 'price': 10000, 'desc': 'Pudding coklat dengan vla vanilla'},
    ]
}

def start(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = user.id
    
    # Reset user session
    user_sessions[user_id] = {'cart': [], 'step': None}
    
    keyboard = [
        [InlineKeyboardButton("📋 Lihat Menu", callback_data="view_menu")],
        [InlineKeyboardButton("🛒 Pesan Sekarang", callback_data="start_order")],
        [InlineKeyboardButton("📞 Hubungi Kami", callback_data="contact")],
        [InlineKeyboardButton("📊 Status Pesanan", callback_data="order_status")]
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
/status - Cek status pesanan
    """
    
    update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

def show_categories(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("🍛 MAKANAN", callback_data="category_makanan")],
        [InlineKeyboardButton("🥤 MINUMAN", callback_data="category_minuman")],
        [InlineKeyboardButton("🍰 DESSERT", callback_data="category_dessert")],
        [InlineKeyboardButton("🛒 Lihat Keranjang", callback_data="view_cart")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "📋 **PILIH KATEGORI MENU**\n\nSilakan pilih kategori menu:"
    
    if update.callback_query:
        update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

def show_menu(update: Update, context: CallbackContext):
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
        [InlineKeyboardButton("📞 Tanya Menu", callback_data="ask_menu")],
        [InlineKeyboardButton("🔙 Kembali", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        update.callback_query.edit_message_text(menu_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        update.message.reply_text(menu_text, reply_markup=reply_markup, parse_mode='Markdown')

def show_category_items(update: Update, context: CallbackContext):
    query = update.callback_query
    category = query.data.replace('category_', '')
    
    if category not in MENU_ITEMS:
        query.edit_message_text("Kategori tidak ditemukan")
        return
    
    items = MENU_ITEMS[category]
    category_name = {
        'makanan': '🍛 MAKANAN',
        'minuman': '🥤 MINUMAN', 
        'dessert': '🍰 DESSERT'
    }[category]
    
    text = f"{category_name}\n\n"
    
    keyboard = []
    for item in items:
        keyboard.append([
            InlineKeyboardButton(
                f"➕ {item['name']} - Rp {item['price']:,}",
                callback_data=f"add_{item['id']}"
            )
        ])
    
    keyboard.extend([
        [InlineKeyboardButton("🛒 Lihat Keranjang", callback_data="view_cart")],
        [InlineKeyboardButton("📋 Kategori Lain", callback_data="view_categories")],
        [InlineKeyboardButton("🔙 Menu Utama", callback_data="back_to_main")]
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    for item in items:
        text += f"• {item['name']} - Rp {item['price']:,}\n"
        text += f"  _{item['desc']}_\n\n"
    
    query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

def add_to_cart(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    item_id = query.data.replace('add_', '')
    
    # Find item in menu
    item = None
    for category in MENU_ITEMS.values():
        for menu_item in category:
            if menu_item['id'] == item_id:
                item = menu_item
                break
        if item:
            break
    
    if not item:
        query.answer("Item tidak ditemukan", show_alert=True)
        return
    
    # Initialize user session if not exists
    if user_id not in user_sessions:
        user_sessions[user_id] = {'cart': [], 'step': None}
    
    # Add to cart
    user_sessions[user_id]['cart'].append(item)
    
    query.answer(f"✅ {item['name']} ditambahkan ke keranjang!")
    
    # Show categories again
    show_categories(update, context)

def view_cart(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    
    if user_id not in user_sessions or not user_sessions[user_id]['cart']:
        text = "🛒 **KERANJANG ANDA**\n\nKeranjang Anda masih kosong."
        keyboard = [
            [InlineKeyboardButton("📋 Lihat Menu", callback_data="view_categories")],
            [InlineKeyboardButton("🔙 Menu Utama", callback_data="back_to_main")]
        ]
    else:
        cart = user_sessions[user_id]['cart']
        total = sum(item['price'] for item in cart)
        
        text = "🛒 **KERANJANG ANDA**\n\n"
        for i, item in enumerate(cart, 1):
            text += f"{i}. {item['name']} - Rp {item['price']:,}\n"
        
        text += f"\n**Total: Rp {total:,}**"
        
        keyboard = [
            [InlineKeyboardButton("➕ Tambah Item", callback_data="view_categories")],
            [InlineKeyboardButton("✅ Checkout", callback_data="checkout")],
            [InlineKeyboardButton("🗑️ Kosongkan Keranjang", callback_data="clear_cart")],
            [InlineKeyboardButton("🔙 Menu Utama", callback_data="back_to_main")]
        ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

def checkout(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    
    if user_id not in user_sessions or not user_sessions[user_id]['cart']:
        query.answer("Keranjang masih kosong!", show_alert=True)
        return
    
    user_sessions[user_id]['step'] = 'waiting_name'
    
    text = """
💰 **CHECKOUT** 🛒

Silakan lengkapi data pemesanan:

📝 **Ketik nama lengkap Anda:**
    """
    
    query.edit_message_text(text, parse_mode='Markdown')

def handle_message(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    text = update.message.text
    
    if user_id not in user_sessions or not user_sessions[user_id].get('step'):
        update.message.reply_text("Silakan ketik /start untuk memulai")
        return
    
    session = user_sessions[user_id]
    
    if session['step'] == 'waiting_name':
        session['customer_name'] = text
        session['step'] = 'waiting_phone'
        update.message.reply_text("📱 **Ketik nomor WhatsApp Anda:**")
        
    elif session['step'] == 'waiting_phone':
        session['phone'] = text
        session['step'] = 'waiting_address'
        update.message.reply_text("🏠 **Ketik alamat pengiriman:**")
        
    elif session['step'] == 'waiting_address':
        session['address'] = text
        session['step'] = None
        
        # Create order
        order_id = create_order(user_id, session)
        
        # Send confirmation
        send_order_confirmation(update, context, order_id, session)
        
        # Clear cart
        session['cart'] = []

def create_order(user_id, session):
    order_id = f"ORD{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    orders[order_id] = {
        'user_id': user_id,
        'customer_name': session['customer_name'],
        'phone': session['phone'],
        'address': session['address'],
        'items': session['cart'].copy(),
        'total': sum(item['price'] for item in session['cart']),
        'status': 'diproses',
        'timestamp': datetime.now().isoformat()
    }
    
    return order_id

def send_order_confirmation(update: Update, context: CallbackContext, order_id: str, session: dict):
    order = orders[order_id]
    
    text = f"""
✅ **PESANAN BERHASIL DIBUAT!**

📋 **No. Pesanan:** `{order_id}`
👤 **Nama:** {order['customer_name']}
📱 **Telepon:** {order['phone']}
🏠 **Alamat:** {order['address']}

🛒 **Detail Pesanan:**
"""
    
    for item in order['items']:
        text += f"• {item['name']} - Rp {item['price']:,}\n"
    
    text += f"\n💰 **Total: Rp {order['total']:,}**"
    text += f"\n\n📊 **Status:** {order['status'].title()}"
    text += f"\n⏰ **Estimasi:** 30-45 menit"
    text += f"\n\n💳 **Metode Pembayaran:**"
    text += f"\n- Transfer Bank (BCA: 123-456-7890)"
    text += f"\n- Tunai (COD)"
    text += f"\n\nGunakan /status untuk cek status pesanan"

    keyboard = [
        [InlineKeyboardButton("📊 Status Pesanan", callback_data="order_status")],
        [InlineKeyboardButton("🛒 Pesan Lagi", callback_data="view_categories")],
        [InlineKeyboardButton("📞 Hubungi Kami", callback_data="contact")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

def order_status(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    
    # Find user's orders
    user_orders = []
    for order_id, order in orders.items():
        if order['user_id'] == user_id:
            user_orders.append((order_id, order))
    
    if not user_orders:
        text = "📊 **STATUS PESANAN**\n\nBelum ada pesanan yang ditemukan."
    else:
        # Get latest order
        latest_order_id, latest_order = user_orders[-1]
        
        text = f"""
📊 **STATUS PESANAN TERAKHIR**

📋 **No. Pesanan:** `{latest_order_id}`
📦 **Items:** {len(latest_order['items'])} item
💰 **Total:** Rp {latest_order['total']:,}
📊 **Status:** {latest_order['status'].title()}
⏰ **Order Time:** {latest_order['timestamp'][:16]}
        """
    
    keyboard = [
        [InlineKeyboardButton("🛒 Pesan Lagi", callback_data="view_categories")],
        [InlineKeyboardButton("🔙 Menu Utama", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

def clear_cart(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    
    if user_id in user_sessions:
        user_sessions[user_id]['cart'] = []
    
    query.answer("✅ Keranjang dikosongkan!")
    view_cart(update, context)

def help_command(update: Update, context: CallbackContext):
    help_text = """
🆘 **BANTUAN PEMESANAN**

**Cara Pesan:**
1. Klik 'Pesan Sekarang' atau ketik /order
2. Pilih kategori menu
3. Tambah item ke keranjang
4. Checkout dan isi data
5. Bayar & tunggu konfirmasi

**Metode Bayar:**
• Transfer Bank (BCA, BRI, Mandiri)
• Tunai (COD - Cash On Delivery)

**Info Layanan:**
• Area pengiriman: Jakarta & Sekitarnya
• Min. pesanan: Rp 25,000
• Estimasi: 30-45 menit

**Problem?** Hubungi: +62 812-3456-7890
    """
    
    update.message.reply_text(help_text, parse_mode='Markdown')

def contact(update: Update, context: CallbackContext):
    contact_text = """
📞 **HUBUNGI KAMI**

📍 **Alamat:**
Jl. Restoran No. 123, Jakarta

📱 **Kontak:**
WhatsApp: +62 812-3456-7890
Telepon: (021) 123-4567

🕒 **Jam Operasional:**
Senin - Minggu: 09:00 - 22:00 WIB

🚗 **Layanan:**
• Dine-in • Take away • Delivery

*Free delivery untuk order > Rp 50,000*
    """
    
    if update.callback_query:
        update.callback_query.edit_message_text(contact_text, parse_mode='Markdown')
    else:
        update.message.reply_text(contact_text, parse_mode='Markdown')

def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    data = query.data
    
    if data == "view_menu":
        show_menu(update, context)
    elif data == "start_order":
        show_categories(update, context)
    elif data == "view_categories":
        show_categories(update, context)
    elif data == "category_makanan":
        show_category_items(update, context)
    elif data == "category_minuman":
        show_category_items(update, context)
    elif data == "category_dessert":
        show_category_items(update, context)
    elif data.startswith("add_"):
        add_to_cart(update, context)
    elif data == "view_cart":
        view_cart(update, context)
    elif data == "checkout":
        checkout(update, context)
    elif data == "clear_cart":
        clear_cart(update, context)
    elif data == "order_status":
        order_status(update, context)
    elif data == "contact":
        contact(update, context)
    elif data == "ask_menu":
        query.edit_message_text("❓ Ada pertanyaan tentang menu? Hubungi kami: +62 812-3456-7890")
    elif data == "back_to_main":
        start(update, context)

def main():
    """Main function"""
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not found!")
        return
    
    updater = Updater(BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    
    # Add handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("menu", show_menu))
    dispatcher.add_handler(CommandHandler("order", show_categories))
    dispatcher.add_handler(CommandHandler("status", order_status))
    dispatcher.add_handler(CommandHandler("help", help_command))
    
    dispatcher.add_handler(CallbackQueryHandler(button_handler))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    logger.info("🤖 Restaurant Bot is running...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()