import os
import json
import logging
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    ChatJoinRequestHandler,
    ChatMemberHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

OWNER_ID = 8796084661

TOKEN_BOT_1 = "8723910838:AAFfWtVYGMX23u1WeboqtCRdc_4oMEvz0jo"
TOKEN_BOT_2 = "8975139578:AAG6sX9SFMz3Fk0Rgb4W16CeSPT2ibMW2xI"
TOKEN_BOT_3 = "8950741154:AAHXRNRR8iVqIo3BB1YqMaRrih-cOvljHaY"

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bots Live 24/7!")

def run_health_check_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

def get_data_file(bot_num):
    return f"bot{bot_num}_data.json"

def load_data(bot_num):
    file_name = get_data_file(bot_num)
    default_data = {
        "admins": [OWNER_ID],
        "users": [],
        "saved_messages": [],
        "leave_link": ""
    }
    if not os.path.exists(file_name):
        return default_data
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            data = json.load(f)
            for k, v in default_data.items():
                data.setdefault(k, v)
            if OWNER_ID not in data["admins"]:
                data["admins"].append(OWNER_ID)
            return data
    except Exception:
        return default_data

def save_data(bot_num, data):
    file_name = get_data_file(bot_num)
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def build_bot_app(token, bot_num):
    app = Application.builder().token(token).build()

    async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
        request = update.chat_join_request
        user = request.from_user
        user_id = user.id

        data = load_data(bot_num)
        if user_id not in data["users"]:
            data["users"].append(user_id)
            save_data(bot_num, data)

        saved_msgs = data.get("saved_messages", [])

        for idx, item in enumerate(saved_msgs):
            try:
                from_chat_id = item.get("from_chat_id")
                message_id = item.get("message_id")
                reply_markup_dict = item.get("reply_markup")

                reply_markup = InlineKeyboardMarkup.de_json(reply_markup_dict, context.bot) if reply_markup_dict else None

                # copy_message प्रीमियम स्टिकर, फोटो, वीडियो और हर तरह के मीडिया को सपोर्ट करता है
                sent_msg = await context.bot.copy_message(
                    chat_id=user_id,
                    from_chat_id=from_chat_id,
                    message_id=message_id,
                    reply_markup=reply_markup
                )

                if idx == 1 and sent_msg:
                    await context.bot.pin_chat_message(
                        chat_id=user_id,
                        message_id=sent_msg.message_id,
                        disable_notification=False
                    )
            except Exception as e:
                logging.error(f"Error copying msg to user {user_id} (Bot {bot_num}): {e}")

    async def handle_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
        result = update.chat_member
        if not result:
            return
        if result.old_chat_member.status in ["member", "administrator"] and result.new_chat_member.status in ["left", "kicked"]:
            user_id = result.from_user.id
            data = load_data(bot_num)
            leave_link = data.get("leave_link", "")

            msg_text = "⚠️ आप चैनल से हट गए हैं!\n\nपुनः जुड़ने के लिए नीचे दिए बटन पर क्लिक करें:"
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Rejoin Channel ↗️", url=leave_link)]]) if leave_link else None

            try:
                await context.bot.send_message(chat_id=user_id, text=msg_text, reply_markup=reply_markup)
            except Exception as e:
                logging.error(f"Error sending leave msg: {e}")

    async def admin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        data = load_data(bot_num)
        if user_id not in data["admins"]:
            return

        admins_list_str = ", ".join([str(a) for a in data["admins"]])
        
        msg_text = (
            f"⚙️ <b>BOT {bot_num} ADMIN PANEL</b>\n\n"
            f"👑 <b>Admins:</b> {admins_list_str}\n"
            f"👥 <b>Total Joined Users:</b> {len(data['users'])}\n"
            f"📦 <b>Saved Messages:</b> {len(data['saved_messages'])}"
        )

        admin_keyboard = [
            [
                InlineKeyboardButton("📢 Send Broadcast", callback_data="btn_broadcast"),
                InlineKeyboardButton("🗑️ Clear All Messages", callback_data="btn_clear")
            ],
            [
                InlineKeyboardButton("➕ Save New Messages", callback_data="btn_start_saving")
            ],
            [
                InlineKeyboardButton("➕ Add Admin", callback_data="btn_add_admin"),
                InlineKeyboardButton("➖ Remove Admin", callback_data="btn_rem_admin")
            ],
            [
                InlineKeyboardButton("🔗 Set Leave Link", callback_data="btn_set_leave")
            ]
        ]

        await update.message.reply_text(msg_text, reply_markup=InlineKeyboardMarkup(admin_keyboard), parse_mode="HTML")

    async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = query.from_user.id
        data = load_data(bot_num)

        if user_id not in data["admins"]:
            await query.answer("❌ Unauthorized!", show_alert=True)
            return

        cb_data = query.data

        if cb_data == "btn_clear":
            data["saved_messages"] = []
            save_data(bot_num, data)
            await query.answer("🗑️ All saved messages deleted!", show_alert=True)
            await query.message.edit_text("🗑️ All saved messages have been cleared.")

        elif cb_data == "btn_start_saving":
            context.user_data["action"] = "saving_messages"
            context.user_data["temp_msgs"] = []
            
            done_keyboard = ReplyKeyboardMarkup([["✅ DONE"]], resize_keyboard=True)
            await query.message.reply_text(
                "📥 <b>Save Mode Active!</b>\n\nअब आप जो-जो मैसेज सेव करना चाहते हैं (टेक्स्ट, फोटो, वीडियो, प्रीमियम स्टीकर या बटन्स वाले मैसेज), बारी-बारी से भेजें।\nसारे मैसेज भेजने के बाद नीचे दिए <b>✅ DONE</b> बटन पर क्लिक करें।",
                parse_mode="HTML",
                reply_markup=done_keyboard
            )
            await query.answer()

        elif cb_data == "btn_broadcast":
            context.user_data["action"] = "wait_broadcast"
            await query.message.reply_text("📢 अब वो मैसेज या मीडिया भेजें जिसे सभी यूज़र्स को ब्रॉडकास्ट करना है:")
            await query.answer()

        elif cb_data == "btn_add_admin":
            context.user_data["action"] = "wait_add_admin"
            await query.message.reply_text("➕ जिसे एडमिन बनाना है उसकी Telegram User ID भेजें:")
            await query.answer()

        elif cb_data == "btn_rem_admin":
            context.user_data["action"] = "wait_rem_admin"
            await query.message.reply_text("➖ जिसे एडमिन से हटाना है उसकी Telegram User ID भेजें:")
            await query.answer()

        elif cb_data == "btn_set_leave":
            context.user_data["action"] = "wait_leave_link"
            await query.message.reply_text("🔗 चैनल का नया Rejoin Link भेजें:")
            await query.answer()

    async def message_collector_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        data = load_data(bot_num)
        if user_id not in data["admins"]:
            return

        action = context.user_data.get("action")
        if not action:
            return

        if action == "saving_messages":
            text = update.message.text
            if text == "✅ DONE":
                temp_msgs = context.user_data.get("temp_msgs", [])
                if temp_msgs:
                    data["saved_messages"].extend(temp_msgs)
                    save_data(bot_num, data)
                    await update.message.reply_text(
                        f"✅ <b>{len(temp_msgs)} Messages Saved Successfully!</b>\nTotal Saved: {len(data['saved_messages'])}",
                        parse_mode="HTML",
                        reply_markup=ReplyKeyboardRemove()
                    )
                else:
                    await update.message.reply_text(
                        "⚠️ कोई मैसेज प्राप्त नहीं हुआ। सेव मोड बंद कर दिया गया है।",
                        reply_markup=ReplyKeyboardRemove()
                    )
                context.user_data["action"] = None
                context.user_data["temp_msgs"] = []
                return

            msg = update.message
            reply_markup_dict = msg.reply_markup.to_dict() if msg.reply_markup else None

            msg_ref = {
                "from_chat_id": msg.chat_id,
                "message_id": msg.message_id,
                "reply_markup": reply_markup_dict
            }

            context.user_data["temp_msgs"].append(msg_ref)
            count = len(context.user_data["temp_msgs"])
            await update.message.reply_text(f"📥 Message #{count} received! और भेजें या <b>✅ DONE</b> पर क्लिक करें।", parse_mode="HTML")

        elif action == "wait_add_admin":
            try:
                new_admin = int(update.message.text.strip())
                if new_admin not in data["admins"]:
                    data["admins"].append(new_admin)
                    save_data(bot_num, data)
                    await update.message.reply_text(f"✅ Admin Added: {new_admin}")
                else:
                    await update.message.reply_text("⚠️ यह ID पहले से एडमिन है।")
            except ValueError:
                await update.message.reply_text("❌ कृपया सही Numeric User ID भेजें।")
            context.user_data["action"] = None

        elif action == "wait_rem_admin":
            try:
                rem_admin = int(update.message.text.strip())
                if rem_admin == OWNER_ID:
                    await update.message.reply_text("❌ Main Owner को नहीं हटाया जा सकता!")
                elif rem_admin in data["admins"]:
                    data["admins"].remove(rem_admin)
                    save_data(bot_num, data)
                    await update.message.reply_text(f"✅ Admin Removed: {rem_admin}")
                else:
                    await update.message.reply_text("⚠️ यह ID एडमिन लिस्ट में नहीं है।")
            except ValueError:
                await update.message.reply_text("❌ कृपया सही Numeric User ID भेजें।")
            context.user_data["action"] = None

        elif action == "wait_leave_link":
            link = update.message.text.strip()
            data["leave_link"] = link
            save_data(bot_num, data)
            await update.message.reply_text(f"✅ Leave Link Saved: {link}")
            context.user_data["action"] = None

        elif action == "wait_broadcast":
            context.user_data["action"] = None
            broadcast_msg = update.message
            await update.message.reply_text("🚀 Broadcasting started...")
            success = 0
            failed = 0
            for u in data["users"]:
                try:
                    await broadcast_msg.copy(chat_id=u)
                    success += 1
                except Exception:
                    failed += 1
            await update.message.reply_text(f"✅ Broadcast Complete!\n\nSuccess: {success}\nFailed: {failed}")

    async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(f"🟢 Bot {bot_num} Active!\n\nAdmin Panel: /admin")

    app.add_handler(ChatJoinRequestHandler(handle_join_request))
    app.add_handler(ChatMemberHandler(handle_chat_member, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(CommandHandler("admin", admin_cmd))
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, message_collector_handler))

    return app

async def main_runner():
    app1 = build_bot_app(TOKEN_BOT_1, 1)
    app2 = build_bot_app(TOKEN_BOT_2, 2)
    app3 = build_bot_app(TOKEN_BOT_3, 3)

    await app1.initialize()
    await app2.initialize()
    await app3.initialize()

    await app1.start()
    await app2.start()
    await app3.start()

    await app1.updater.start_polling(allowed_updates=["message", "chat_join_request", "chat_member", "callback_query"], drop_pending_updates=True)
    await app2.updater.start_polling(allowed_updates=["message", "chat_join_request", "chat_member", "callback_query"], drop_pending_updates=True)
    app3_polling = app3.updater.start_polling(allowed_updates=["message", "chat_join_request", "chat_member", "callback_query"], drop_pending_updates=True)
    if asyncio.iscoroutine(app3_polling):
        await app3_polling

    logging.info("All 3 bots started successfully!")

    # अनंत समय तक बोट को जिंदा रखने के लिए
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    # हेल्थ चेक सर्वर बैकग्राउंड में चलाना (Render के पोर्ट बाइंडिंग इश्यू से बचाने के लिए)
    threading.Thread(target=run_health_check_server, daemon=True).start()
    
    try:
        asyncio.run(main_runner())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bots stopped gracefully.")
