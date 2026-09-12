import os
import json
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
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
BROADCAST_USERS = set()

# Token (Bot 3)
TOKEN_BOT_3 = "8723910838:AAGDn-3HPeDMMIpjkpuKYgD152txrt1XgTA"

# ==============================================================================
# WEB SERVER (Hosting के लिए)
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
    default_data = {
        "users": [],
        "pending_requests": [],
        "saved_messages": [],
        "auto_approve": False,
        "start_message": {
            "type": "text",
            "text": "👋 **Welcome!**\nनीचे दिए गए कीबोर्ड बटन्स का उपयोग करें:",
            "reply_markup": None
        },
        "keyboard_buttons": [
            {"btn": "🎁 Claim Reward", "reply": "🎉 Your reward link: https://t.me/... (Yahan apna link daal le)"},
            {"btn": "📢 Join Channel", "reply": "🔗 Join our main channel here: https://t.me/..."},
            {"btn": "ℹ️ Help / Info", "reply": "ℹ️ Ye bot join request automate karne aur updates bhejne ke liye hai."},
            {"btn": "📞 Support", "reply": "💬 Contact Admin for support: @YourUsername"}
        ]
    }
    
    if not os.path.exists(DATA_FILE):
        return default_data
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            for key in default_data:
                if key not in data:
                    data[key] = default_data[key]
            return data
    except:
        return default_data

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Data save error: {e}")

def get_user_keyboard(data):
    kb_data = data.get("keyboard_buttons", [])
    buttons = []
    row = []
    for item in kb_data:
        row.append(KeyboardButton(item["btn"]))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

# ==============================================================================
# HANDLERS: /start & USER KEYBOARD RESPONSES
# ==============================================================================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = load_data()
    
    if user_id not in data["users"]:
        data["users"].append(user_id)
        save_data(data)

    user_markup = get_user_keyboard(data)
    
    # 1. सेट किया गया /start वेलकम मैसेज और उसके इनलाइन बटन्स भेजना
    s_msg = data.get("start_message", {})
    try:
        m_type = s_msg.get("type", "text")
        markup_dict = s_msg.get("reply_markup")
        # यहाँ इनलाइन बटन्स को रिक्रिएट किया जा रहा है ताकि वे मैसेज के साथ जाएं
        inline_markup = InlineKeyboardMarkup.de_json(markup_dict, context.bot) if markup_dict else None

        if m_type == "photo":
            await context.bot.send_photo(chat_id=user_id, photo=s_msg.get("file_id"), caption=s_msg.get("caption", ""), reply_markup=inline_markup)
        elif m_type == "video":
            await context.bot.send_video(chat_id=user_id, video=s_msg.get("file_id"), caption=s_msg.get("caption", ""), reply_markup=inline_markup)
        elif m_type == "voice":
            await context.bot.send_voice(chat_id=user_id, voice=s_msg.get("file_id"), caption=s_msg.get("caption", ""), reply_markup=inline_markup)
        elif m_type == "audio":
            await context.bot.send_audio(chat_id=user_id, audio=s_msg.get("file_id"), caption=s_msg.get("caption", ""), reply_markup=inline_markup)
        elif m_type == "document":
            await context.bot.send_document(chat_id=user_id, document=s_msg.get("file_id"), caption=s_msg.get("caption", ""), reply_markup=inline_markup)
        else:
            await context.bot.send_message(chat_id=user_id, text=s_msg.get("text", "Welcome!"), reply_markup=inline_markup)
    except Exception as e:
        logging.error(f"Error sending start message: {e}")

    # 2. यूजर के नीचे वाले Reply Keyboard बटन्स भेजने के लिए एक अलग से मैसेज
    await context.bot.send_message(
        chat_id=user_id,
        text="👇 नीचे दिए गए बटन्स का उपयोग करें:",
        reply_markup=user_markup
    )

    # 3. अन्य सेव किए गए मैसेज भेजना
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
            elif m_type == "voice":
                await context.bot.send_voice(chat_id=user_id, voice=file_id, caption=caption, reply_markup=markup)
            elif m_type == "audio":
                await context.bot.send_audio(chat_id=user_id, audio=file_id, caption=caption, reply_markup=markup)
            elif m_type == "document":
                await context.bot.send_document(chat_id=user_id, document=file_id, caption=caption, reply_markup=markup)
            else:
                await context.bot.send_message(chat_id=user_id, text=text, reply_markup=markup)
        except Exception as e:
            logging.error(f"Error sending saved msg: {e}")

async def handle_user_keyboard_clicks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        if ADMIN_ID in BROADCAST_USERS:
            return 

    text = update.message.text
    data = load_data()
    user_markup = get_user_keyboard(data)

    for item in data.get("keyboard_buttons", []):
        if text == item["btn"]:
            await update.message.reply_text(item["reply"], reply_markup=user_markup)
            return

# ==============================================================================
# ADMIN PANEL
# ==============================================================================
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized!")
        return
    
    data = load_data()
    u_count = len(data.get("users", []))
    m_count = len(data.get("saved_messages", []))
    p_count = len(data.get("pending_requests", []))
    auto_status = "🟢 ON" if data.get("auto_approve", False) else "🔴 OFF"

    keyboard = [
        [InlineKeyboardButton("🔵 📢 Broadcast Message", callback_data="btn_broadcast")],
        [InlineKeyboardButton("🟡 📥 Save Media/Msg (/save)", callback_data="btn_save_info")],
        [InlineKeyboardButton("🟢 ⚙️ Set /start Welcome Msg", callback_data="btn_set_start")],
        [InlineKeyboardButton("🟣 ⌨️ Edit Keyboard Buttons & Replies", callback_data="btn_edit_kb")],
        [InlineKeyboardButton(f"🟠 ✅ Approve All Requests ({p_count})", callback_data="btn_approve_all")],
        [InlineKeyboardButton(f"🩵 🔄 Auto-Approve: {auto_status}", callback_data="btn_toggle_auto")],
        [InlineKeyboardButton("🔴 🗑️ Delete All Saved Msgs", callback_data="btn_delete_all")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"⚙️ **[Admin Control Panel]**\n\n"
        f"👥 Total Users: `{u_count}`\n"
        f"📦 Saved Messages: `{m_count}`\n"
        f"⏳ Pending Requests: `{p_count}`\n\n"
        f"नीचे दिए गए विकल्पों में से चुनें:",
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
        await query.message.reply_text("📢 **Broadcast Mode On!**\nअब जो भी मैसेज/वॉयस आप यहाँ भेजेंगे, वह सभी यूजर्स को ब्रॉडकास्ट हो जाएगा।")

    elif action == "btn_save_info":
        await query.answer()
        await query.message.reply_text("💡 किसी भी मैसेज (वॉयस, फोटो या टेक्स्ट) पर रिप्लाई करके `/save` लिखें, वह सेव हो जाएगा।")

    elif action == "btn_set_start":
        await query.answer()
        await query.message.reply_text("💡 **Welcome Message सेट करने का तरीका:**\nजो मैसेज (बटन वाले, फोटो, वीडियो, वॉइस या टेक्स्ट) आप `/start` पर रखना चाहते हैं, उस पर Reply करके `/setstart` लिखें।")

    elif action == "btn_edit_kb":
        await query.answer()
        kb_list = data.get("keyboard_buttons", [])
        text = "⌨️ **Current Keyboard Buttons & Replies:**\n\n"
        for i, kb in enumerate(kb_list, 1):
            text += f"{i}. **Button:** `{kb['btn']}`\n   **Reply:** `{kb['reply']}`\n\n"
        text += "✏️ इन्हें बदलने के लिए इस फॉर्मेट में लिखकर भेजें:\n`/editkb [बटन नंबर] | [नया बटन नाम] | [नया रिप्लाई]`\n\nउदाहरण:\n`/editkb 1 | 🎁 Check Bonus | ये रहा आपका बोनस लिंक: ...`"
        await query.message.reply_text(text, parse_mode="Markdown")

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
        await query.message.edit_text(f"✅ Successfully approved {success_count} requests!")

    elif action == "btn_toggle_auto":
        current = data.get("auto_approve", False)
        data["auto_approve"] = not current
        save_data(data)
        
        u_count = len(data.get("users", []))
        m_count = len(data.get("saved_messages", []))
        p_count = len(data.get("pending_requests", []))
        auto_status = "🟢 ON" if data["auto_approve"] else "🔴 OFF"

        keyboard = [
            [InlineKeyboardButton("🔵 📢 Broadcast Message", callback_data="btn_broadcast")],
            [InlineKeyboardButton("🟡 📥 Save Media/Msg (/save)", callback_data="btn_save_info")],
            [InlineKeyboardButton("🟢 ⚙️ Set /start Welcome Msg", callback_data="btn_set_start")],
            [InlineKeyboardButton("🟣 ⌨️ Edit Keyboard Buttons & Replies", callback_data="btn_edit_kb")],
            [InlineKeyboardButton(f"🟠 ✅ Approve All Requests ({p_count})", callback_data="btn_approve_all")],
            [InlineKeyboardButton(f"🩵 🔄 Auto-Approve: {auto_status}", callback_data="btn_toggle_auto")],
            [InlineKeyboardButton("🔴 🗑️ Delete All Saved Msgs", callback_data="btn_delete_all")]
        ]
        await query.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
        await query.answer(f"Auto-Approve is now {auto_status}", show_alert=True)

    elif action == "btn_delete_all":
        data["saved_messages"] = []
        save_data(data)
        await query.answer("🗑️ All saved messages deleted!", show_alert=True)
        await query.message.reply_text("🗑️ सभी सेव किए गए मैसेज डिलीट कर दिए गए हैं।")

# ==============================================================================
# ADMIN CUSTOM COMMANDS (/setstart & /editkb)
# ==============================================================================
async def set_start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    reply = update.message.reply_to_message
    if not reply:
        await update.message.reply_text("❌ किसी मैसेज (इनलाइन बटन वाले, फोटो, वीडियो, वॉइस या टेक्स्ट) पर Reply करके `/setstart` लिखें।")
        return

    data = load_data()
    start_data = {}
    reply_markup_dict = reply.reply_markup.to_dict() if reply.reply_markup else None

    if reply.photo:
        start_data = {"type": "photo", "file_id": reply.photo[-1].file_id, "caption": reply.caption or "", "reply_markup": reply_markup_dict}
    elif reply.video:
        start_data = {"type": "video", "file_id": reply.video.file_id, "caption": reply.caption or "", "reply_markup": reply_markup_dict}
    elif reply.voice:
        start_data = {"type": "voice", "file_id": reply.voice.file_id, "caption": reply.caption or "", "reply_markup": reply_markup_dict}
    elif reply.audio:
        start_data = {"type": "audio", "file_id": reply.audio.file_id, "caption": reply.caption or "", "reply_markup": reply_markup_dict}
    elif reply.document:
        start_data = {"type": "document", "file_id": reply.document.file_id, "caption": reply.caption or "", "reply_markup": reply_markup_dict}
    elif reply.text:
        start_data = {"type": "text", "text": reply.text, "reply_markup": reply_markup_dict}
    else:
        await update.message.reply_text("❌ Unsupported message type!")
        return

    data["start_message"] = start_data
    save_data(data)
    await update.message.reply_text("✅ **New /start Welcome Message (with Inline Buttons) Set Successfully!**")

async def edit_keyboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    text = update.message.text
    try:
        parts = text.replace("/editkb", "").split("|")
        if len(parts) < 3:
            await update.message.reply_text("❌ गलत फॉर्मेट! इस तरह भेजें:\n`/editkb 1 | बटन नाम | रिप्लाई मैसेज`", parse_mode="Markdown")
            return
        
        index = int(parts[0].strip()) - 1
        new_btn = parts[1].strip()
        new_reply = parts[2].strip()

        data = load_data()
        if 0 <= index < len(data["keyboard_buttons"]):
            data["keyboard_buttons"][index]["btn"] = new_btn
            data["keyboard_buttons"][index]["reply"] = new_reply
            save_data(data)
            await update.message.reply_text(f"✅ **Keyboard Button #{index+1} Updated Successfully!**\n\nButton: `{new_btn}`\nReply: `{new_reply}`", parse_mode="Markdown", reply_markup=get_user_keyboard(data))
        else:
            await update.message.reply_text("❌ अमान्य बटन नंबर! सही नंबर चुनें।")
    except Exception as e:
        await update.message.reply_text(f"❌ एरर: कृपया सही फॉर्मेट का उपयोग करें।\n`/editkb 1 | बटन नाम | रिप्लाई मैसेज`")

async def save_message_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    reply = update.message.reply_to_message
    if not reply:
        await update.message.reply_text("❌ किसी भी मैसेज पर Reply करके `/save` लिखें।")
        return

    data = load_data()
    msg_data = {}
    reply_markup_dict = reply.reply_markup.to_dict() if reply.reply_markup else None

    if reply.photo:
        msg_data = {"type": "photo", "file_id": reply.photo[-1].file_id, "caption": reply.caption or "", "reply_markup": reply_markup_dict}
    elif reply.video:
        msg_data = {"type": "video", "file_id": reply.video.file_id, "caption": reply.caption or "", "reply_markup": reply_markup_dict}
    elif reply.voice:
        msg_data = {"type": "voice", "file_id": reply.voice.file_id, "caption": reply.caption or "", "reply_markup": reply_markup_dict}
    elif reply.audio:
        msg_data = {"type": "audio", "file_id": reply.audio.file_id, "caption": reply.caption or "", "reply_markup": reply_markup_dict}
    elif reply.document:
        msg_data = {"type": "document", "file_id": reply.document.file_id, "caption": reply.caption or "", "reply_markup": reply_markup_dict}
    elif reply.text:
        msg_data = {"type": "text", "text": reply.text, "reply_markup": reply_markup_dict}
    else:
        await update.message.reply_text("❌ Unsupported message type!")
        return

    data["saved_messages"].append(msg_data)
    save_data(data)
    await update.message.reply_text(f"✅ **Message Saved Successfully!** Total saved: {len(data['saved_messages'])}")

async def clear_messages_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    data = load_data()
    data["saved_messages"] = []
    save_data(data)
    await update.message.reply_text("🗑️ All saved messages cleared!")

# ==============================================================================
# JOIN REQUEST HANDLER
# ==============================================================================
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

        user_markup = get_user_keyboard(data)

        # 1. /start वेलकम मैसेज और उसके इनलाइन बटन्स भेजना
        s_msg = data.get("start_message", {})
        try:
            m_type = s_msg.get("type", "text")
            markup_dict = s_msg.get("reply_markup")
            inline_markup = InlineKeyboardMarkup.de_json(markup_dict, context.bot) if markup_dict else None

            if m_type == "photo":
                await context.bot.send_photo(chat_id=user_id, photo=s_msg.get("file_id"), caption=s_msg.get("caption", ""), reply_markup=inline_markup)
            elif m_type == "video":
                await context.bot.send_video(chat_id=user_id, video=s_msg.get("file_id"), caption=s_msg.get("caption", ""), reply_markup=inline_markup)
            elif m_type == "voice":
                await context.bot.send_voice(chat_id=user_id, voice=s_msg.get("file_id"), caption=s_msg.get("caption", ""), reply_markup=inline_markup)
            elif m_type == "audio":
                await context.bot.send_audio(chat_id=user_id, audio=s_msg.get("file_id"), caption=s_msg.get("caption", ""), reply_markup=inline_markup)
            elif m_type == "document":
                await context.bot.send_document(chat_id=user_id, document=s_msg.get("file_id"), caption=s_msg.get("caption", ""), reply_markup=inline_markup)
            else:
                await context.bot.send_message(chat_id=user_id, text=s_msg.get("text", "Welcome!"), reply_markup=inline_markup)
        except Exception as e:
            logging.error(f"Error sending start msg in join req: {e}")

        # 2. यूजर कीबोर्ड बटन्स भेजना
        await context.bot.send_message(
            chat_id=user_id,
            text="👇 नीचे दिए गए बटन्स का उपयोग करें:",
            reply_markup=user_markup
        )

        # 3. अन्य सेव किए गए मैसेज भेजना
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
                elif m_type == "voice":
                    await context.bot.send_voice(chat_id=user_id, voice=file_id, caption=caption, reply_markup=markup)
                elif m_type == "audio":
                    await context.bot.send_audio(chat_id=user_id, audio=file_id, caption=caption, reply_markup=markup)
                elif m_type == "document":
                    await context.bot.send_document(chat_id=user_id, document=file_id, caption=caption, reply_markup=markup)
                else:
                    await context.bot.send_message(chat_id=user_id, text=text, reply_markup=markup)
            except Exception as e:
                logging.error(f"Error sending to user: {e}")

    except Exception as e:
        logging.error(f"Join request error: {e}")

# ==============================================================================
# BROADCAST HANDLER
# ==============================================================================
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
                elif reply.voice:
                    await context.bot.send_voice(chat_id=uid, voice=reply.voice.file_id, caption=reply.caption or "", reply_markup=reply.reply_markup)
                elif reply.audio:
                    await context.bot.send_audio(chat_id=uid, audio=reply.audio.file_id, caption=reply.caption or "", reply_markup=reply.reply_markup)
                elif reply.document:
                    await context.bot.send_document(chat_id=uid, document=reply.document.file_id, caption=reply.caption or "", reply_markup=reply.reply_markup)
                else:
                    await context.bot.send_message(chat_id=uid, text=reply.text or "", reply_markup=reply.reply_markup)
                success += 1
            except Exception:
                failed += 1

        await update.message.reply_text(f"📢 **Broadcast Complete!**\n\n✅ Sent: {success}\n❌ Failed: {failed}")

# ==============================================================================
# MAIN APPLICATION
# ==============================================================================
if __name__ == "__main__":
    threading.Thread(target=run_web_server, daemon=True).start()

    app = Application.builder().token(TOKEN_BOT_3).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("save", save_message_command))
    app.add_handler(CommandHandler("setstart", set_start_command))
    app.add_handler(CommandHandler("editkb", edit_keyboard_command))
    app.add_handler(CommandHandler("clear_msgs", clear_messages_command))
    app.add_handler(CallbackQueryHandler(admin_callback_handler))
    app.add_handler(ChatJoinRequestHandler(handle_join_request))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_keyboard_clicks))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND & ~filters.TEXT, handle_admin_broadcast))
    
    logging.info("Bot is starting polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)
