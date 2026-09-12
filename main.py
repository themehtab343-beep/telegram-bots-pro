import os
import json
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ChatJoinRequestHandler
)

# Logging Setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Common Admin ID
ADMIN_ID = 8796084661

# ==============================================================================
# BOT TOKENS
# ==============================================================================
TOKEN_BOT_1 = "8723910838:AAFfWtVYGMX23u1WeboqtCRdc_4oMEvz0jo"
TOKEN_BOT_2 = "8796084661:AAGYHSa2u3dMG0aM6gQviG89Seolt1xi34c"
TOKEN_BOT_3 = "8950741154:AAHXRNRR8iVqIo3BB1YqMaRrih-cOvljHaY"

# ==============================================================================
# LIGHTWEIGHT WEB SERVER (Hosting के लिए ताकि Exit 1 न आए)
# ==============================================================================
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bots are running 24/7 successfully!")

    def log_message(self, format, *args):
        #ालतू HTTP logs को छिपाने के लिए ताकि कंसोल साफ़ रहे
        return

def run_web_server():
    try:
        port = int(os.environ.get("PORT", 8080))
        server = HTTPServer(("0.0.0.0", port), SimpleHandler)
        logging.info(f"Web server started on port {port}")
        server.serve_forever()
    except Exception as e:
        logging.error(f"Web server error: {e}")

# ==============================================================================
# BOT 3 DATA MANAGER (Isolated File: bot3_data.json)
# ==============================================================================
DATA_FILE_3 = "bot3_data.json"

def load_data_3():
    if not os.path.exists(DATA_FILE_3):
        return {"users": [], "saved_messages": []}
    try:
        with open(DATA_FILE_3, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"users": [], "saved_messages": []}

def save_data_3(data):
    try:
        with open(DATA_FILE_3, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Error saving data: {e}")

# ==============================================================================
# BOT 3 HANDLERS
# ==============================================================================

async def handle_join_request_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        request = update.chat_join_request
        user = request.from_user
        user_id = user.id

        data = load_data_3()

        if user_id not in data["users"]:
            data["users"].append(user_id)
            save_data_3(data)

        # Admin Alert
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"🚨 <b>[Bot 3] New Join Request!</b>\n👤 <b>Name:</b> {user.first_name}\n🆔 <b>User ID:</b> <code>{user_id}</code>",
                parse_mode="HTML"
            )
        except Exception as e:
            logging.error(f"Failed to alert admin: {e}")

        # Send Saved Messages to User
        saved_msgs = data.get("saved_messages", [])
        for idx, item in enumerate(saved_msgs):
            try:
                sent_msg = None
                msg_type = item.get("type")
                file_id = item.get("file_id")
                caption = item.get("caption", "")

                if msg_type == "photo":
                    sent_msg = await context.bot.send_photo(chat_id=user_id, photo=file_id, caption=caption)
                elif msg_type == "video":
                    sent_msg = await context.bot.send_video(chat_id=user_id, video=file_id, caption=caption)
                elif msg_type == "voice":
                    sent_msg = await context.bot.send_voice(chat_id=user_id, voice=file_id, caption=caption)
                elif msg_type == "audio":
                    sent_msg = await context.bot.send_audio(chat_id=user_id, audio=file_id, caption=caption)
                elif msg_type == "document":
                    sent_msg = await context.bot.send_document(chat_id=user_id, document=file_id, caption=caption)
                else:
                    sent_msg = await context.bot.send_message(chat_id=user_id, text=item.get("text", ""))

                # Auto-Pin Second Message (Index 1)
                if idx == 1 and sent_msg:
                    await context.bot.pin_chat_message(
                        chat_id=user_id,
                        message_id=sent_msg.message_id,
                        disable_notification=False
                    )
            except Exception as e:
                logging.error(f"Error sending message to {user_id}: {e}")
    except Exception as e:
        logging.error(f"Join request error: {e}")

async def start_command_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🟢 <b>[Bot 3] Active & Ready 24/7!</b>\n\nAdmin Control: /admin", parse_mode="HTML")

async def save_command_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        return

    reply = update.message.reply_to_message
    if not reply:
        await update.message.reply_text("❌ Reply to a message with /save to store it for Bot 3.")
        return

    data = load_data_3()
    msg_data = {}

    if reply.photo:
        msg_data = {"type": "photo", "file_id": reply.photo[-1].file_id, "caption": reply.caption or ""}
    elif reply.video:
        msg_data = {"type": "video", "file_id": reply.video.file_id, "caption": reply.caption or ""}
    elif reply.voice:
        msg_data = {"type": "voice", "file_id": reply.voice.file_id, "caption": reply.caption or ""}
    elif reply.audio:
        msg_data = {"type": "audio", "file_id": reply.audio.file_id, "caption": reply.caption or ""}
    elif reply.document:
        msg_data = {"type": "document", "file_id": reply.document.file_id, "caption": reply.caption or ""}
    elif reply.text:
        msg_data = {"type": "text", "text": reply.text}

    data["saved_messages"].append(msg_data)
    save_data_3(data)
    await update.message.reply_text(f"✅ <b>Message Saved for Bot 3!</b> Total: {len(data['saved_messages'])}", parse_mode="HTML")

async def clear_command_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    data = load_data_3()
    data["saved_messages"] = []
    save_data_3(data)
    await update.message.reply_text("🗑️ All saved messages cleared for Bot 3!")

async def admin_command_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    data = load_data_3()
    u_count = len(data.get("users", []))
    m_count = len(data.get("saved_messages", []))
    await update.message.reply_text(
        f"⚙️ <b>[Bot 3 Admin Panel]</b>\n\n👥 Total Users: <code>{u_count}</code>\n📦 Saved Messages: <code>{m_count}</code>\n\nCommands:\n/save - Reply to save message\n/clear_msgs - Reset saved messages",
        parse_mode="HTML"
    )

# ==============================================================================
# BOT RUNNERS (Safe with Try-Except)
# ==============================================================================

def run_bot_1():
    try:
        app1 = Application.builder().token(TOKEN_BOT_1).build()
        app1.run_polling()
    except Exception as e:
        logging.error(f"Bot 1 failed to start: {e}")

def run_bot_2():
    try:
        app2 = Application.builder().token(TOKEN_BOT_2).build()
        app2.run_polling()
    except Exception as e:
        logging.error(f"Bot 2 failed to start: {e}")

def run_bot_3():
    try:
        app3 = Application.builder().token(TOKEN_BOT_3).build()
        app3.add_handler(ChatJoinRequestHandler(handle_join_request_3))
        app3.add_handler(CommandHandler("start", start_command_3))
        app3.add_handler(CommandHandler("save", save_command_3))
        app3.add_handler(CommandHandler("clear_msgs", clear_command_3))
        app3.add_handler(CommandHandler("admin", admin_command_3))
        app3.run_polling()
    except Exception as e:
        logging.error(f"Bot 3 failed to start: {e}")

# ==============================================================================
# MAIN MULTI-THREADING EXECUTION
# ==============================================================================
if __name__ == "__main__":
    # Web server thread (होस्टिंग पोर्ट को चालू रखने के लिए)
    t_web = threading.Thread(target=run_web_server, daemon=True)
    t_web.start()

    t1 = threading.Thread(target=run_bot_1)
    t2 = threading.Thread(target=run_bot_2)
    t3 = threading.Thread(target=run_bot_3)

    t1.start()
    t2.start()
    t3.start()

    # मुख्य धागे को बंद होने से रोकने के लिए
    threading.Event().wait()
