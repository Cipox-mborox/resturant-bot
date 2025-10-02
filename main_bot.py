import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, Filters
import json
from datetime import datetime

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== CONFIGURATION ====================
# GANTI DENGAN ID TELEGRAM ANDA
# Cara dapatkan ID: buka @userinfobot di Telegram, kirim pesan
ADMIN_IDS = [7521156999] # ⚠️ GANTI INI DENGAN ID ANDA!

ORDERS_FILE = 'orders.json'

# ==================== DATA STORAGE ====================
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

def is_admin(user_id):
    """Check if user is admin"""
    return user_id in ADMIN_IDS

# ==================== MENU DATA ====================
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

# In-memory sessions
user_sessions = {}

# ==================== CUSTOMER FUNCTIONS ====================
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = user.id
    
    # Reset user session
    user_sessions[user_id] = {'cart': [], 'step': None}
    
    # Check if user is admin
    if is_admin(user_id):
        keyboard = [
            [InlineKeyboardButton("🛒 Pesan Makanan", callback_data="view_categories")],
            [InlineKeyboardButton("👑 Admin Panel", callback_data="admin_start")],
            [InlineKeyboardButton("📞 Hubungi Kami", callback_data="contact")]
        ]
    else:
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
    """
    
    if is_admin(user_id):
        welcome_text += "\n👑 *Anda login sebagai Admin*"
    
    welcome_text += """

**Perintah tersedia:**
/menu - Lihat menu lengkap
/order - Buat pesanan baru  
/help - Bantuan pemesanan
/status - Cek status pesanan
    """
    
    update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

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
        [InlineKeyboardButton("🔙 Menu Utama", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        update.callback_query.edit_message_text(menu_text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        update.message.reply_text(menu_text, reply_markup=reply_markup, parse_mode='Markdown')

def show_categories(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("🍛 MAKANAN", callback_data="category_makanan")],
        [InlineKeyboardButton("🥤 MINUMAN", callback_data="category_minuman")],
        [InlineKeyboardButton("🍰 DESSERT", callback_data="category_dessert")],
        [InlineKeyboardButton("🛒 Lihat Keranjang", callback_data="view_cart")],
        [InlineKeyboardButton("🔙 Menu Utama", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "📋 **PILIH KATEGORI MENU**\n\nSilakan pilih kategori menu:"
    
    if update.callback_query:
        update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

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
    
    orders = load_orders()
    
    orders[order_id] = {
        'user_id': user_id,
        'customer_name': session['customer_name'],
        'phone': session['phone'],
        'address': session['address'],
        'items': session['cart'].copy(),
        'total': sum(item['price'] for item in session['cart']),
        'status': 'baru',
        'timestamp': datetime.now().isoformat()
    }
    
    save_orders(orders)
    return order_id

def send_order_confirmation(update: Update, context: CallbackContext, order_id: str, session: dict):
    orders = load_orders()
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
    orders = load_orders()
    
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
        
        status_emoji = {
            'baru': '🆕',
            'diproses': '👨‍🍳',
            'dikirim': '🚗',
            'selesai': '✅'
        }.get(latest_order['status'], '📝')
        
        text = f"""
📊 **STATUS PESANAN TERAKHIR**

📋 **No. Pesanan:** `{latest_order_id}`
📦 **Items:** {len(latest_order['items'])} item
💰 **Total:** Rp {latest_order['total']:,}
📊 **Status:** {latest_order['status'].title()} {status_emoji}
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

# ==================== ADMIN FUNCTIONS ====================
def admin_start(update: Update, context: CallbackContext):
    """Admin panel start"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        update.message.reply_text("❌ Akses ditolak. Hanya admin yang bisa mengakses.")
        return
    
    keyboard = [
        [InlineKeyboardButton("📊 DAFTAR PESANAN", callback_data="admin_list_orders")],
        [InlineKeyboardButton("⏳ PESANAN BARU", callback_data="admin_new_orders")],
        [InlineKeyboardButton("👨‍🍳 PESANAN DIPROSES", callback_data="admin_processing_orders")],
        [InlineKeyboardButton("📈 STATISTIK", callback_data="admin_stats")],
        [InlineKeyboardButton("🛒 Mode Customer", callback_data="back_to_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = """
👑 **DASHBOARD ADMIN RESTORAN**

Selamat datang di Admin Panel!

**Fitur yang tersedia:**
• 📊 Lihat semua pesanan
• ⏳ Kelola pesanan baru  
• 👨‍🍳 Update status pesanan
• 📈 Lihat statistik penjualan
    """
    
    if update.callback_query:
        update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')

def admin_list_orders(update: Update, context: CallbackContext):
    """Show all orders with filters"""
    query = update.callback_query
    user_id = query.from_user.id
    
    if not is_admin(user_id):
        query.answer("Akses ditolak")
        return
    
    orders = load_orders()
    
    if not orders:
        query.edit_message_text("📭 Tidak ada pesanan")
        return
    
    keyboard = [
        [InlineKeyboardButton("🆕 Baru", callback_data="admin_filter_new"),
         InlineKeyboardButton("👨‍🍳 Diproses", callback_data="admin_filter_processing")],
        [InlineKeyboardButton("🚗 Dikirim", callback_data="admin_filter_delivery"),
         InlineKeyboardButton("✅ Selesai", callback_data="admin_filter_completed")],
        [InlineKeyboardButton("📋 Semua", callback_data="admin_filter_all")],
        [InlineKeyboardButton("🔙 Dashboard", callback_data="admin_back_dashboard")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    total_orders = len(orders)
    new_orders = sum(1 for o in orders.values() if o['status'] == 'baru')
    processing_orders = sum(1 for o in orders.values() if o['status'] == 'diproses')
    
    text = f"""
📊 **DAFTAR PESANAN**

📈 **Statistik:**
• Total Pesanan: {total_orders}
• Pesanan Baru: {new_orders}
• Sedang Diproses: {processing_orders}

Pilih filter untuk melihat pesanan:
    """
    
    query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

def admin_show_orders(update: Update, context: CallbackContext, status_filter=None):
    """Show orders based on filter"""
    query = update.callback_query
    user_id = query.from_user.id
    
    if not is_admin(user_id):
        query.answer("Akses ditolak")
        return
    
    orders = load_orders()
    
    if status_filter and status_filter != 'all':
        filtered_orders = {k: v for k, v in orders.items() if v['status'] == status_filter}
    else:
        filtered_orders = orders
    
    if not filtered_orders:
        status_text = {
            'baru': 'baru',
            'diproses': 'diproses', 
            'dikirim': 'dikirim',
            'selesai': 'selesai',
            None: 'apapun'
        }.get(status_filter, 'apapun')
        
        query.edit_message_text(f"📭 Tidak ada pesanan {status_text}")
        return
    
    # Show first order
    order_ids = list(filtered_orders.keys())
    order_id = order_ids[0]
    order = filtered_orders[order_id]
    
    text = format_order_detail(order_id, order)
    
    # Status update buttons
    keyboard = []
    status_buttons = []
    if order['status'] == 'baru':
        status_buttons.append(InlineKeyboardButton("👨‍🍳 Proses", callback_data=f"admin_status_processing_{order_id}"))
    elif order['status'] == 'diproses':
        status_buttons.append(InlineKeyboardButton("🚗 Kirim", callback_data=f"admin_status_delivery_{order_id}"))
    elif order['status'] == 'dikirim':
        status_buttons.append(InlineKeyboardButton("✅ Selesai", callback_data=f"admin_status_completed_{order_id}"))
    
    if status_buttons:
        keyboard.append(status_buttons)
    
    keyboard.extend([
        [InlineKeyboardButton("📞 Hubungi Customer", callback_data=f"admin_contact_{order_id}")],
        [InlineKeyboardButton("📊 Kembali ke List", callback_data="admin_list_orders")],
        [InlineKeyboardButton("🔙 Dashboard", callback_data="admin_back_dashboard")]
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

def format_order_detail(order_id, order):
    """Format order details for display"""
    items_text = "\n".join([f"• {item['name']} - Rp {item['price']:,}" for item in order['items']])
    
    status_emoji = {
        'baru': '🆕',
        'diproses': '👨‍🍳',
        'dikirim': '🚗',
        'selesai': '✅'
    }.get(order['status'], '📝')
    
    text = f"""
{status_emoji} **PESANAN {order_id}**

👤 **Customer:** {order['customer_name']}
📱 **Telepon:** {order['phone']}
🏠 **Alamat:** {order['address']}

🛒 **Items:**
{items_text}

💰 **Total:** Rp {order['total']:,}
📊 **Status:** {order['status'].title()} {status_emoji}
⏰ **Order Time:** {order['timestamp'][:16]}
    """
    
    return text

def admin_update_status(update: Update, context: CallbackContext):
    """Update order status"""
    query = update.callback_query
    user_id = query.from_user.id
    
    if not is_admin(user_id):
        query.answer("Akses ditolak")
        return
    
    data = query.data
    order_id = data.split('_')[-1]
    new_status = data.split('_')[2]  # processing, delivery, completed
    
    status_map = {
        'processing': 'diproses',
        'delivery': 'dikirim', 
        'completed': 'selesai'
    }
    
    orders = load_orders()
    
    if order_id not in orders:
        query.answer("Pesanan tidak ditemukan")
        return
    
    old_status = orders[order_id]['status']
    orders[order_id]['status'] = status_map[new_status]
    
    save_orders(orders)
    
    query.answer(f"✅ Status diupdate ke {status_map[new_status].title()}")
    
    # Refresh the order view
    admin_show_orders(update, context, status_map[new_status])

def admin_stats(update: Update, context: CallbackContext):
    """Show statistics"""
    query = update.callback_query
    user_id = query.from_user.id
    
    if not is_admin(user_id):
        query.answer("Akses ditolak")
        return
    
    orders = load_orders()
    
    if not orders:
        query.edit_message_text("📊 Belum ada data statistik")
        return
    
    # Calculate stats
    total_orders = len(orders)
    total_revenue = sum(order['total'] for order in orders.values())
    
    status_counts = {}
    for order in orders.values():
        status = order['status']
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # Today's orders
    today = datetime.now().date().isoformat()
    today_orders = sum(1 for order in orders.values() if order['timestamp'].startswith(today))
    today_revenue = sum(order['total'] for order in orders.values() if order['timestamp'].startswith(today))
    
    text = f"""
📈 **STATISTIK RESTORAN**

📅 **Hari Ini:**
• Pesanan: {today_orders}
• Pendapatan: Rp {today_revenue:,}

📊 **Total:**
• Total Pesanan: {total_orders}
• Total Pendapatan: Rp {total_revenue:,}

📋 **Status Pesanan:**
• 🆕 Baru: {status_counts.get('baru', 0)}
• 👨‍🍳 Diproses: {status_counts.get('diproses', 0)}
• 🚗 Dikirim: {status_counts.get('dikirim', 0)}
• ✅ Selesai: {status_counts.get('selesai', 0)}
    """
    
    keyboard = [
        [InlineKeyboardButton("🔄 Refresh", callback_data="admin_stats")],
        [InlineKeyboardButton("🔙 Dashboard", callback_data="admin_back_dashboard")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

def admin_contact_customer(update: Update, context: CallbackContext):
    """Show customer contact info"""
    query = update.callback_query
    user_id = query.from_user.id
    
    if not is_admin(user_id):
        query.answer("Akses ditolak")
        return
    
    order_id = query.data.split('_')[-1]
    orders = load_orders()
    
    if order_id not in orders:
        query.answer("Pesanan tidak ditemukan")
        return
    
    order = orders[order_id]
    
    text = f"""
📞 **KONTAK CUSTOMER**

📋 **Order ID:** {order_id}
👤 **Nama:** {order['customer_name']}
📱 **WhatsApp:** {order['phone']}
🏠 **Alamat:** {order['address']}

**Link WhatsApp:**
https://wa.me/{order['phone'].replace('+', '').replace(' ', '')}?text=Halo%20{order['customer_name'].replace(' ', '%20')}%2C%20saya%20dari%20restoran...
    """
    
    keyboard = [
        [InlineKeyboardButton("🔙 Kembali ke Pesanan", callback_data=f"admin_back_to_order_{order_id}")],
        [InlineKeyboardButton("📊 List Pesanan", callback_data="admin_list_orders")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

# ==================== MAIN HANDLER ====================
def button_handler(update: Update, context: CallbackContext):
    """Handle all button callbacks"""
    query = update.callback_query
    query.answer()
    
    data = query.data
    
    # Customer handlers
    if data == "back_to_main":
        start(update, context)
    elif data == "view_menu":
        show_menu(update, context)
    elif data == "start_order" or data == "view_categories":
        show_categories(update, context)
    elif data in ["category_makanan", "category_minuman", "category_dessert"]:
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
    
    # Admin handlers
    elif data == "admin_start":
        admin_start(update, context)
    elif data == "admin_back_dashboard":
        admin_start(update, context)
    elif data == "admin_list_orders":
        admin_list_orders(update, context)
    elif data == "admin_new_orders":
        admin_show_orders(update, context, 'baru')
    elif data == "admin_processing_orders":
        admin_show_orders(update, context, 'diproses')
    elif data == "admin_stats":
        admin_stats(update, context)
    elif data.startswith("admin_filter_"):
        filter_type = data.replace('admin_filter_', '')
        if filter_type == 'all':
            admin_show_orders(update, context, None)
        else:
            admin_show_orders(update, context, filter_type)
    elif data.startswith("admin_status_"):
        admin_update_status(update, context)
    elif data.startswith("admin_contact_"):
        admin_contact_customer(update, context)
    elif data.startswith("admin_back_to_order_"):
        order_id = data.replace('admin_back_to_order_', '')
        orders = load_orders()
        if order_id in orders:
            admin_show_orders(update, context, orders[order_id]['status'])

def main():
    """Main function"""
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not found!")
        return
    
    # ⚠️ IMPORTANT: Set your Telegram ID here!
    # Cara dapatkan ID: buka @userinfobot di Telegram
    global ADMIN_IDS
    ADMIN_IDS = [7521156999] # ⚠️ GANTI INI DENGAN ID TELEGRAM ANDA!
    
    updater = Updater(BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    
    # Command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("menu", show_menu))
    dispatcher.add_handler(CommandHandler("order", show_categories))
    dispatcher.add_handler(CommandHandler("status", order_status))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("admin", admin_start))  # ✅ Admin command
    
    # Message handlers
    dispatcher.add_handler(CallbackQueryHandler(button_handler))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    logger.info("🤖 Restaurant Bot + Admin is running...")
    logger.info(f"👑 Admin IDs: {ADMIN_IDS}")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()