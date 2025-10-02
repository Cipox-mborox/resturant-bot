import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler
import json
from datetime import datetime

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Admin user IDs (ganti dengan ID Telegram admin Anda)
ADMIN_IDS = [7521156999] # Ganti dengan ID admin sebenarnya

# File untuk menyimpan orders (simulasi database)
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

def is_admin(user_id):
    """Check if user is admin"""
    return user_id in ADMIN_IDS

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
        [InlineKeyboardButton("🚗 PESANAN DIANTAR", callback_data="admin_delivery_orders")],
        [InlineKeyboardButton("✅ PESANAN SELESAI", callback_data="admin_completed_orders")],
        [InlineKeyboardButton("📈 STATISTIK", callback_data="admin_stats")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = """
👑 **DASHBOARD ADMIN RESTORAN**

Selamat datang di Admin Panel!

**Fitur yang tersedia:**
• 📊 Lihat semua pesanan
• ⏳ Kelola pesanan baru  
• 👨‍🍳 Update status pesanan
• 🚗 Lacak pengantaran
• ✅ Lihat pesanan selesai
• 📈 Lihat statistik penjualan
    """
    
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
    
    # Show first order with pagination
    order_ids = list(filtered_orders.keys())
    current_index = 0
    
    if context.user_data.get('current_order_index') is not None:
        current_index = context.user_data['current_order_index']
    
    if current_index >= len(order_ids):
        current_index = 0
    
    order_id = order_ids[current_index]
    order = filtered_orders[order_id]
    
    text = format_order_detail(order_id, order)
    
    # Pagination keyboard
    keyboard = []
    
    # Status update buttons
    status_buttons = []
    if order['status'] == 'baru':
        status_buttons.append(InlineKeyboardButton("👨‍🍳 Proses", callback_data=f"admin_status_processing_{order_id}"))
    elif order['status'] == 'diproses':
        status_buttons.append(InlineKeyboardButton("🚗 Kirim", callback_data=f"admin_status_delivery_{order_id}"))
    elif order['status'] == 'dikirim':
        status_buttons.append(InlineKeyboardButton("✅ Selesai", callback_data=f"admin_status_completed_{order_id}"))
    
    if status_buttons:
        keyboard.append(status_buttons)
    
    # Navigation buttons
    nav_buttons = []
    if len(order_ids) > 1:
        if current_index > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Sebelumnya", callback_data=f"admin_prev_{status_filter}"))
        if current_index < len(order_ids) - 1:
            nav_buttons.append(InlineKeyboardButton("Selanjutnya ➡️", callback_data=f"admin_next_{status_filter}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.extend([
        [InlineKeyboardButton("📞 Hubungi Customer", callback_data=f"admin_contact_{order_id}")],
        [InlineKeyboardButton("📊 Kembali ke List", callback_data="admin_list_orders")],
        [InlineKeyboardButton("🔙 Dashboard", callback_data="admin_back_dashboard")]
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Store current index for pagination
    context.user_data['current_order_index'] = current_index
    context.user_data['current_order_ids'] = order_ids
    context.user_data['current_filter'] = status_filter
    
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
    
    # Notify customer (in real implementation, you'd send message to customer)
    logger.info(f"Order {order_id} status changed from {old_status} to {status_map[new_status]}")
    
    query.answer(f"✅ Status diupdate ke {status_map[new_status].title()}")
    
    # Refresh the order view
    admin_show_orders(update, context, context.user_data.get('current_filter'))

def admin_navigate_orders(update: Update, context: CallbackContext):
    """Navigate between orders"""
    query = update.callback_query
    user_id = query.from_user.id
    
    if not is_admin(user_id):
        query.answer("Akses ditolak")
        return
    
    data = query.data
    direction = data.split('_')[1]  # prev or next
    status_filter = data.split('_')[2]  # filter
    
    current_index = context.user_data.get('current_order_index', 0)
    order_ids = context.user_data.get('current_order_ids', [])
    
    if direction == 'prev' and current_index > 0:
        current_index -= 1
    elif direction == 'next' and current_index < len(order_ids) - 1:
        current_index += 1
    
    context.user_data['current_order_index'] = current_index
    
    # Reload with new index
    orders = load_orders()
    order_id = order_ids[current_index]
    order = orders[order_id]
    
    text = format_order_detail(order_id, order)
    
    # Recreate keyboard (similar to admin_show_orders)
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
    
    nav_buttons = []
    if len(order_ids) > 1:
        if current_index > 0:
            nav_buttons.append(InlineKeyboardButton("⬅️ Sebelumnya", callback_data=f"admin_prev_{status_filter}"))
        if current_index < len(order_ids) - 1:
            nav_buttons.append(InlineKeyboardButton("Selanjutnya ➡️", callback_data=f"admin_next_{status_filter}"))
    
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.extend([
        [InlineKeyboardButton("📞 Hubungi Customer", callback_data=f"admin_contact_{order_id}")],
        [InlineKeyboardButton("📊 Kembali ke List", callback_data="admin_list_orders")],
        [InlineKeyboardButton("🔙 Dashboard", callback_data="admin_back_dashboard")]
    ])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

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
https://wa.me/{order['phone'].replace('+', '').replace(' ', '')}?text=Halo%20{order['customer_name']}%2C%20saya%20dari%20restoran...
    """
    
    keyboard = [
        [InlineKeyboardButton("🔙 Kembali ke Pesanan", callback_data=f"admin_back_to_order_{order_id}")],
        [InlineKeyboardButton("📊 List Pesanan", callback_data="admin_list_orders")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')

def admin_button_handler(update: Update, context: CallbackContext):
    """Handle admin button callbacks"""
    query = update.callback_query
    query.answer()
    
    data = query.data
    
    if data == "admin_back_dashboard":
        admin_start(update, context)
    elif data == "admin_list_orders":
        admin_list_orders(update, context)
    elif data == "admin_new_orders":
        admin_show_orders(update, context, 'baru')
    elif data == "admin_processing_orders":
        admin_show_orders(update, context, 'diproses')
    elif data == "admin_delivery_orders":
        admin_show_orders(update, context, 'dikirim')
    elif data == "admin_completed_orders":
        admin_show_orders(update, context, 'selesai')
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
    elif data.startswith("admin_prev_") or data.startswith("admin_next_"):
        admin_navigate_orders(update, context)
    elif data.startswith("admin_contact_"):
        admin_contact_customer(update, context)
    elif data.startswith("admin_back_to_order_"):
        order_id = data.replace('admin_back_to_order_', '')
        orders = load_orders()
        if order_id in orders:
            admin_show_orders(update, context, orders[order_id]['status'])

def main():
    """Main admin bot"""
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not found!")
        return
    
    # Update ADMIN_IDS dengan ID Telegram Anda
    global ADMIN_IDS
    # Ganti dengan ID Telegram admin sebenarnya
    # Cara dapatkan ID Telegram: kirim message ke @userinfobot di Telegram
    ADMIN_IDS = [7521156999] # GANTI DENGAN ID ANDA
    
    updater = Updater(BOT_TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    
    # Admin handlers
    dispatcher.add_handler(CommandHandler("admin", admin_start))
    dispatcher.add_handler(CallbackQueryHandler(admin_button_handler, pattern="^admin_"))
    
    logger.info("👑 Admin Bot is running...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()