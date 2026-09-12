import os
import json
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ChatJoinRequestHandler,
    ContextTypes,
    filters
)

# Logging Setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Common Admin ID
ADMIN_ID = 8796084661
DATA_FILE = "bot3_data.json"

# Broadcast State Track करने के लिए
BROADCAST_USERS = set()

# नए टोकन्स यहाँ सेट कर दिए गए हैं
TOKEN_BOT_1 = "8950741154:AAHFel5umWqJdksC9NQ89hEE9sURQHH2Zys"
TOKEN_BOT_2 = "8975139578:AAFaNj0-IoWo5AHjH8b1nDccTCT1lIXoCcE"
TOKEN_BOT_3 = "8723910838:AAGDn-3HPeDMMIpjkpuKYgD152txrt1XgTA"

# ==============================================================================
# WEB SERVER (Hosting के लिए ताकि App बंद न हो)
# ==============================================================================
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active and running 24/7!")
    def log_message(self, format, *args):
        return

def run_web_server():
    try:
        port = int(os.environ.get("PORT", 8080))
        server = HTTPServer(("0.0.0.0", port), SimpleHandler)
        server.serve_forever()
    except Exception as e:
        logging.error(f"Web server error: {e}")

# ==============================================================================
# DATA MANAGER
# ==============================================================================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"users": [], "pending_requests": [], "saved_messages": [], "auto_approve": False}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"users": [], "pending_requests": [], "saved_messages": [], "auto_approve": False}

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Data save error: {e}")

# ==============================================================================
# BOT 3 HANDLERS & INLINE ADMIN PANEL
# ==============================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🟢 **Bot 3 is Active!**\n\nType /admin to open the Admin Panel.")

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized!")
        return
    
    data = load_data()
    u_count = len(data.get("users", []))
    m_count = len(data.get("saved_messages", []))
    p_count = len(data.get("pending_requests", []))
    auto_status = "🟢 ON" if data.get("auto_approve", False) else "🔴 OFF"

    # रंग-बिरंगे और सुंदर Inline Buttons (No keyboard buttons)
    keyboard = [
        [InlineKeyboardButton("📢 Broadcast Message", callback_data="btn_broadcast")],
        [InlineKeyboardButton("📥 Save Message Info (/save)", callback_data="btn_save_info")],
        [InlineKeyboardButton(f"✅ Approve All Pending Requests ({p_count})", callback_data="btn_approve_all")],
        [InlineKeyboardButton(f"🔄 Auto-Approve Mode: {auto_status}", callback_data="btn_toggle_auto")],
        [InlineKeyboardButton("🗑️ Delete All Saved Messages", callback_data="btn_delete_all")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"⚙️ **[Admin Control Panel]**\n\n"
        f"👥 Total Users: `{u_count}`\n"
        f"📦 Saved Messages: `{m_count}`\n"
        f"⏳ Pending Join Requests: `{p_count}`\n\n"
        f"नीचे दिए गए बटन्स का उपयोग करें:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != ADMIN_ID:
        await query.answer("❌ Unauthorized!", show_alert=True)
        return

    data = load_data()
    action = query.data

    if action == "btn_broadcast":
        BROADCAST_USERS.add(ADMIN_ID)
        await query.answer()
        await query.message.reply_text("📢 **Broadcast Mode On!**\n\nअब जो भी मैसेज (Text, Photo, Video आदि) आप यहाँ भेजेंगे, वह सभी यूजर्स को उनके बटन्स के साथ भेज दिया जाएगा।")

    elif action == "btn_save_info":
        await query.answer()
        await query.message.reply_text("💡 **Message Save karne ka tarika:**\nकिसी भी मैसेज (बटन वाले मैसेज सहित) पर रिप्लाई करके `/save` लिखें, वह सेव हो जाएगा।")

    elif action == "btn_approve_all":
        pending = data.get("pending_requests", [])
        success_count = 0
        for req in pending:
            try:
                await context.bot.approve_chat_request(chat_id=req["chat_id"], user_id=req["user_id"])
                success_count += 1
            except Exception as e:
                logging.error(f"Approve error: {e}")
        
        data["pending_requests"] = []
        save_data(data)
        await query.answer(f"✅ {success_count} requests approved!", show_alert=True)
        await query.message.edit_text(f"✅ Successfully approved {success_count} requests! Panel refreshed.")

    elif action == "btn_toggle_auto":
        current = data.get("auto_approve", False)
        data["auto_approve"] = not current
        save_data(data)
        
        u_count = len(data.get("users", []))
        m_count = len(data.get("saved_messages", []))
        p_count = len(data.get("pending_requests", []))
        auto_status = "🟢 ON" if data["auto_approve"] else "🔴 OFF"

        keyboard = [
            [InlineKeyboardButton("📢 Broadcast Message", callback_data="btn_broadcast")],
            [InlineKeyboardButton("📥 Save Message Info (/save)", callback_data="btn_save_info")],
            [InlineKeyboardButton(f"✅ Approve All Pending Requests ({p_count})", callback_data="btn_approve_all")],
            [InlineKeyboardButton(f"🔄 Auto-Approve Mode: {auto_status}", callback_data="btn_toggle_auto")],
            [InlineKeyboardButton("🗑️ Delete All Saved Messages", callback_data="btn_delete_all")]
        ]
        await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
        await query.answer(f"Auto-Approve is now {auto_status}", show_alert=True)

    elif action == "btn_delete_all":
        data["saved_messages"] = []
        save_data(data)
        await query.answer("🗑️ All saved messages deleted!", show_alert=True)
        await query.message.reply_text("🗑️ सभी सेव किए गए मैसेज डिलीट कर दिए गए हैं।")

async def save_message_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    reply = update.message.reply_to_message
    if not reply:
        await update.message.reply_text("❌ किसी मैसेज पर Reply करके `/save` लिखें।")
        return

    data = load_data()
    msg_data = {}

    reply_markup_dict = None
    if reply.reply_markup:
        reply_markup_dict = reply.reply_markup.to_dict()

    if reply.photo:
        msg_data = {"type": "photo", "file_id": reply.photo[-1].file_id, "caption": reply.caption or "", "reply_markup": reply_markup_dict}
    elif reply.video:
        msg_data = {"type": "video", "file_id": reply.video.file_id, "caption": reply.caption or "", "reply_markup": reply_markup_dict}
    elif reply.document:
        msg_data = {"type": "document", "file_id": reply.document.file_id, "caption": reply.caption or "", "reply_markup": reply_markup_dict}
    elif reply.text:
        msg_data = {"type": "text", "text": reply.text, "reply_markup": reply_markup_dict}
    else:
        await update.message.reply_text("❌ Ye message type supported nahi hai!")
        return

    data["saved_messages"].append(msg_data)
    save_data(data)
    await update.message.reply_text(f"✅ **Message Saved Successfully!** Total saved: {len(data['saved_messages'])}\n(साथ में इसके बटन्स भी सेव हो गए हैं)")

async def clear_messages_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    data = load_data()
    data["saved_messages"] = []
    save_data(data)
    await update.message.reply_text("🗑️ All saved messages cleared!")

# Join Request Handler
async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        request = update.chat_join_request
        user = request.from_user
        user_id = user.id
        chat_id = request.chat.id

        data = load_data()
        
        if user_id not in data["users"]:
            data["users"].append(user_id)

        req_info = {"user_id": user_id, "chat_id": chat_id}
        if req_info not in data["pending_requests"]:
            data["pending_requests"].append(req_info)
        
        save_data(data)

        if data.get("auto_approve", False):
            await context.bot.approve_chat_request(chat_id=chat_id, user_id=user_id)
            if req_info in data["pending_requests"]:
                data["pending_requests"].remove(req_info)
                save_data(data)

        saved_msgs = data.get("saved_messages", [])
        for item in saved_msgs:
            try:
                m_type = item.get("type")
                file_id = item.get("file_id")
                caption = item.get("caption", "")
                text = item.get("text", "")
                markup_dict = item.get("reply_markup")
                
                markup = InlineKeyboardMarkup.de_json(markup_dict, context.bot) if markup_dict else None

                if m_type == "photo":
                    await context.bot.send_photo(chat_id=user_id, photo=file_id, caption=caption, reply_markup=markup)
                elif m_type == "video":
                    await context.bot.send_video(chat_id=user_id, video=file_id, caption=caption, reply_markup=markup)
                elif m_type == "document":
                    await context.bot.send_document(chat_id=user_id, document=file_id, caption=caption, reply_markup=markup)
                else:
                    await context.bot.send_message(chat_id=user_id, text=text, reply_markup=markup)
            except Exception as e:
                logging.error(f"Error sending message to user {user_id}: {e}")

    except Exception as e:
        logging.error(f"Join request error: {e}")

# Broadcast Handler
async def handle_admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if ADMIN_ID in BROADCAST_USERS:
        BROADCAST_USERS.remove(ADMIN_ID)
        data = load_data()
        users = data.get("users", [])
        
        success = 0
        failed = 0
        
        reply = update.message
        for uid in users:
            try:
                if reply.photo:
                    await context.bot.send_photo(chat_id=uid, photo=reply.photo[-1].file_id, caption=reply.caption or "", reply_markup=reply.reply_markup)
                elif reply.video:
                    await context.bot.send_video(chat_id=uid, video=reply.video.file_id, caption=reply.caption or "", reply_markup=reply.reply_markup)
                elif reply.document:
                    await context.bot.send_document(chat_id=uid, document=reply.document.file_id, caption=reply.caption or "", reply_markup=reply.reply_markup)
                else:
                    await context.bot.send_message(chat_id=uid, text=reply.text or "", reply_markup=reply.reply_markup)
                success += 1
            except Exception:
                failed += 1

        await update.message.reply_text(f"📢 **Broadcast Complete!**\n\n✅ Sent: {success}\n❌ Failed: {failed}")

# ==============================================================================
# BOT RUNNERS
# ==============================================================================
def run_bot_1():
    try:
        app = Application.builder().token(TOKEN_BOT_1).build()
        app.run_polling()
    except Exception as e:
        logging.error(f"Bot 1 error: {e}")

def run_bot_2():
    try:
        app = Application.builder().token(TOKEN_BOT_2).build()
        app.run_polling()
    except Exception as e:
        logging.error(f"Bot 2 error: {e}")

def run_bot_3():
    try:
        app = Application.builder().token(TOKEN_BOT_3).build()
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("admin", admin_command))
        app.add_handler(CommandHandler("save", save_message_command))
        app.add_handler(CommandHandler("clear_msgs", clear_messages_command))
        app.add_handler(CallbackQueryHandler(admin_callback_handler))
        app.add_handler(ChatJoinRequestHandler(handle_join_request))
        app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_admin_broadcast))
        app.run_polling()
    except Exception as e:
        logging.error(f"Bot 3 error: {e}")

if __name__ == "__main__":
    threading.Thread(target=run_web_server, daemon=True).start()

    threading.Thread(target=run_bot_1).start()
    threading.Thread(target=run_bot_2).start()
    threading.Thread(target=run_bot_3).start()

    threading.Event().wait()
