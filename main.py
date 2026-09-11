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

# स्वास्थ्य जांच (Health Check) सर्वर - Render के लिए जरूरी
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

# डेटा मैनेजमेंट (JSON Storage)
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

# बॉट एप्लीकेशन और कमांड्स बनाना
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
        
        # यूजर ट्रैकिंग
        if user_id not in data["users"]:
            data["users"].append(user_id)
            save_data(bot_num, data)

        leave_link = data.get("leave_link", "")
        reply_markup = None
        if leave_link:
            reply_markup = InlineKeyboardMarkup(
                [[InlineKeyboardButton("📢 Join Channel / Support", url=leave_link)]]
            )

        await message.reply_text(
            f"🟢 **Bot {bot_num} is Active & Ready!**\n\n"
            f"Welcome! Send your content or use admin controls if you are authorized.",
            reply_markup=reply_markup
        )

    # एडमिन पैनल और ब्रॉडकास्ट कमांड
    @app.on_message(filters.command("admin") & filters.private)
    async def admin_panel(client, message):
        user_id = message.from_user.id
        data = load_data(bot_num)

        if user_id not in data["admins"]:
            return await message.reply_text("❌ You are not authorized to use the admin panel.")

        total_users = len(data["users"])
        leave_link = data.get("leave_link", "Not Set")

        text = (
            f"👑 **Bot {bot_num} Admin Panel**\n\n"
            f"👥 Total Users: `{total_users}`\n"
            f"🔗 Current Leave Link: `{leave_link}`\n\n"
            f"**Commands:**\n"
            f"• `/broadcast <message>` - Send message to all users\n"
            f"• `/setlink <url>` - Set or update join/leave link"
        )
        await message.reply_text(text)

    @app.on_message(filters.command("setlink") & filters.private)
    async def set_link(client, message):
        user_id = message.from_user.id
        data = load_data(bot_num)

        if user_id not in data["admins"]:
            return message.stop_propagation()

        if len(message.command) < 2:
            return await message.reply_text("⚠️ Please provide a link. Example: `/setlink https://t.me/yourlink`")

        new_link = message.command[1]
        data["leave_link"] = new_link
        save_data(bot_num, data)
        await message.reply_text(f"✅ Successfully updated leave link to:\n`{new_link}`")

    @app.on_message(filters.command("broadcast") & filters.private)
    async def broadcast_msg(client, message):
        user_id = message.from_user.id
        data = load_data(bot_num)

        if user_id not in data["admins"]:
            return message.stop_propagation()

        if not message.reply_to_message:
            return await message.reply_text("⚠️ Please reply to a message that you want to broadcast!")

        target_users = data["users"]
        if not target_users:
            return await message.reply_text("❌ No users found to broadcast.")

        status_msg = await message.reply_text("📢 Broadcast started...")
        success = 0
        failed = 0

        for uid in target_users:
            try:
                await message.reply_to_message.copy(chat_id=uid)
                success += 1
                await asyncio.sleep(0.1) # फ्लडवेट रोकने के लिए छोटा डिले
            except Exception:
                failed += 1

        await status_msg.edit_text(
            f"✅ **Broadcast Completed!**\n\n"
            f"Successful: `{success}`\n"
            f"Failed: `{failed}`"
        )

    return app

async def main():
    try:
        await start_web_server()
        
        # तीनों बॉट्स को एक साथ इनिशियलाइज और स्टार्ट करना
        app1 = create_bot_app(1, BOT_TOKENS[1])
        app2 = create_bot_app(2, BOT_TOKENS[2])
        app3 = create_bot_app(3, BOT_TOKENS[3])

        await app1.start()
        await app2.start()
        await app3.start()

        logging.info("All 3 Bots Started Successfully with Clean Setup!")
        await asyncio.Event().wait()
    except Exception as e:
        logging.critical(f"Critical error in main: {e}", exc_info=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Fatal error: {e}")
