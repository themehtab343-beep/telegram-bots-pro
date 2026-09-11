import os
import json
import logging
import asyncio
from aiohttp import web
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

OWNER_ID = 8796084661
API_ID = 36845944
API_HASH = "52a5e3343ba1edfe88ca570b42d15e7d"

BOT_TOKENS = {
    1: "8723910838:AAFfWtVYGMX23u1WeboqtCRdc_4oMEvz0jo",
    2: "8975139578:AAG6sX9SFMz3Fk0Rgb4W16CeSPT2ibMW2xI",
    3: "8950741154:AAHXRNRR8iVqIo3BB1YqMaRrih-cOvljHaY"
}

user_states = {}

async def handle_ping(request):
    return web.Response(text="Bots Live 24/7!")

async def start_web_server():
    try:
        app = web.Application()
        app.router.add_get("/", handle_ping)
        runner = web.AppRunner(app)
        await runner.setup()
        port = int(os.environ.get("PORT", 8080))
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        logging.info(f"Health check server running on port {port}")
    except Exception as e:
        logging.error(f"Web server error: {e}")

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

def create_bot_app(bot_num, token):
    app = Client(
        name=f"bot_{bot_num}",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=token,
        in_memory=True
    )

    @app.on_message(filters.command("start") & filters.private)
    async def start_cmd(client, message):
        user_id = message.from_user.id
        data = load_data(bot_num)
        
        if user_id not in data["users"]:
            data["users"].append(user_id)
            save_data(bot_num, data)

        saved_msgs = data.get("saved_messages", [])
        leave_link = data.get("leave_link", "")

        if saved_msgs:
            for item in saved_msgs:
                try:
                    chat_id = item.get("chat_id")
                    msg_id = item.get("msg_id")
                    
                    markup = None
                    if leave_link:
                        markup = InlineKeyboardMarkup([[InlineKeyboardButton("📢 Join Channel / Support", url=leave_link)]])

                    await client.copy_message(
                        chat_id=user_id,
                        from_chat_id=chat_id,
                        message_id=msg_id,
                        reply_markup=markup
                    )
                    await asyncio.sleep(0.2)
                except Exception as e:
                    logging.error(f"Error sending start message: {e}")
        else:
            await message.reply_text("🟢 **Welcome!** Bot is active.")

    @app.on_message(filters.command("admin") & filters.private)
    async def admin_panel(client, message):
        user_id = message.from_user.id
        data = load_data(bot_num)

        if user_id not in data["admins"]:
            return await message.reply_text("❌ You are not authorized.")

        total_users = len(data["users"])
        total_saved = len(data["saved_messages"])
        admins_list = ", ".join(map(str, data['admins']))

        text = (
            f"⚙️ **BOT {bot_num} ADMIN PANEL**\n\n"
            f"👑 **Admins:** `{admins_list}`\n"
            f"👥 **Total Joined Users:** `{total_users}`\n"
            f"📦 **Saved Messages:** `{total_saved}`"
        )

        # आपके पुराने और बिल्कुल सही लेआउट वाले बटन्स
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Send Broadcast", callback_data="bc_start"),
             InlineKeyboardButton("🗑️ Clear All Messages", callback_data="bc_clear")],
            [InlineKeyboardButton("➕ Save New Messages", callback_data="bc_save_new")],
            [InlineKeyboardButton("➕ Add Admin", callback_data="add_admin"),
             InlineKeyboardButton("➖ Remove Admin", callback_data="rem_admin")],
            [InlineKeyboardButton("🔗 Set Leave Link", callback_data="set_link")]
        ])

        await message.reply_text(text, reply_markup=keyboard)

    @app.on_callback_query()
    async def admin_callbacks(client, callback_query):
        user_id = callback_query.from_user.id
        data = load_data(bot_num)

        if user_id not in data["admins"]:
            return await callback_query.answer("❌ You are not authorized!", show_alert=True)

        action = callback_query.data

        if action == "bc_start":
            saved_msgs = data.get("saved_messages", [])
            target_users = data["users"]
            if not saved_msgs:
                return await callback_query.answer("⚠️ No saved messages found!", show_alert=True)
            if not target_users:
                return await callback_query.answer("❌ No users found.", show_alert=True)

            status_msg = await callback_query.message.edit_text("📢 Broadcast started...")
            success, failed = 0, 0

            for uid in target_users:
                for item in saved_msgs:
                    try:
                        await client.copy_message(
                            chat_id=uid,
                            from_chat_id=item["chat_id"],
                            message_id=item["msg_id"]
                        )
                        success += 1
                        await asyncio.sleep(0.1)
                    except Exception:
                        failed += 1

            await status_msg.edit_text(f"✅ **Broadcast Completed!**\nSuccess: `{success}`\nFailed: `{failed}`")

        elif action == "bc_clear":
            data["saved_messages"] = []
            save_data(bot_num, data)
            await callback_query.answer("🗑️ Cleared!", show_alert=True)
            await callback_query.message.edit_text("✅ All saved messages cleared successfully.")

        elif action == "bc_save_new":
            user_states[user_id] = {"bot_num": bot_num, "mode": "saving"}
            data["saved_messages"] = []
            save_data(bot_num, data)
            
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅ DONE", callback_data="save_done")]])
            await callback_query.message.reply_text(
                "📥 **Message Saving Mode Active!**\n\nअब आप जो भी मैसेज, मीडिया या **प्रीमियम स्टीकर** भेजेंगे, वो सेव हो जाएगा। भेजने के बाद नीचे **DONE** पर क्लिक करें।",
                reply_markup=keyboard
            )
            await callback_query.answer()

        elif action == "save_done":
            if user_id in user_states:
                del user_states[user_id]
            total = len(load_data(bot_num)["saved_messages"])
            await callback_query.message.edit_text(f"✅ **{total} Messages/Stickers Saved Successfully!**")

        elif action == "set_link":
            user_states[user_id] = {"bot_num": bot_num, "mode": "set_link"}
            await callback_query.message.reply_text("🔗 कृपया नया लीव/ज्वाइन लिंक (URL) भेजें:")
            await callback_query.answer()

        elif action == "add_admin":
            user_states[user_id] = {"bot_num": bot_num, "mode": "add_admin"}
            await callback_query.message.reply_text("➕ एडमिन की User ID लिखकर भेजें:")
            await callback_query.answer()

        elif action == "rem_admin":
            user_states[user_id] = {"bot_num": bot_num, "mode": "rem_admin"}
            await callback_query.message.reply_text("➖ हटाने के लिए एडमिन की User ID लिखकर भेजें:")
            await callback_query.answer()

    @app.on_message(filters.private & ~filters.command(["start", "admin", "broadcast", "setlink"]))
    async def handle_user_input(client, message):
        user_id = message.from_user.id
        data = load_data(bot_num)

        if user_id in data["admins"] and user_id in user_states:
            state = user_states[user_id]
            if state["bot_num"] == bot_num:
                mode = state["mode"]

                if mode == "saving":
                    # प्रीमियम स्टीकर और सभी प्रकार के मैसेज/मीडिया सेव करने के लिए
                    data["saved_messages"].append({
                        "chat_id": message.chat.id,
                        "msg_id": message.id
                    })
                    save_data(bot_num, data)
                    await message.reply_text(f"📌 Message # {len(data['saved_messages'])} saved! और भेजें या नीचे DONE दबाएँ।")
                    return

                elif mode == "set_link":
                    new_link = message.text.strip()
                    data["leave_link"] = new_link
                    save_data(bot_num, data)
                    del user_states[user_id]
                    await message.reply_text(f"✅ Leave Link updated to:\n`{new_link}`")
                    return

                elif mode == "add_admin":
                    try:
                        new_id = int(message.text.strip())
                        if new_id not in data["admins"]:
                            data["admins"].append(new_id)
                            save_data(bot_num, data)
                        del user_states[user_id]
                        await message.reply_text(f"✅ User `{new_id}` is now an admin!")
                    except ValueError:
                        await message.reply_text("❌ Valid numeric ID दें.")
                    return

                elif mode == "rem_admin":
                    try:
                        rem_id = int(message.text.strip())
                        if rem_id == OWNER_ID:
                            await message.reply_text("⚠️ Owner remove नहीं हो सकता!")
                        elif rem_id in data["admins"]:
                            data["admins"].remove(rem_id)
                            save_data(bot_num, data)
                            await message.reply_text(f"✅ Admin `{rem_id}` removed!")
                        else:
                            await message.reply_text("❌ ID नहीं मिली.")
                        del user_states[user_id]
                    except ValueError:
                        await message.reply_text("❌ Valid ID दें.")
                    return

    return app

async def main():
    try:
        await start_web_server()
        
        app1 = create_bot_app(1, BOT_TOKENS[1])
        app2 = create_bot_app(2, BOT_TOKENS[2])
        app3 = create_bot_app(3, BOT_TOKENS[3])

        await app1.start()
        await app2.start()
        await app3.start()

        logging.info("All 3 Bots Started Successfully!")
        await asyncio.Event().wait()
    except Exception as e:
        logging.critical(f"Critical error: {e}", exc_info=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Fatal error: {e}")
