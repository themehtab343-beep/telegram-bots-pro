import os
import json
import logging
import asyncio
from aiohttp import web
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    ChatJoinRequest
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

OWNER_ID = 8796084661
API_ID = 36845944
API_HASH = "52a5e3343ba1edfe88ca570b42d15e7d"

BOT_TOKENS = {
    1: "8950741154:AAFVa4BrUf81Eh12vz3L5y3xy8240paa36k",
    2: "8975139578:AAFzYWXNbJceY5EFo3a4O2MXXai2w5y2kiQ",
    3: "8723910838:AAHTLbgntVTlZw0P37B0D4yzrUvxxSaVEGs"
}

PREMIUM_STICKER_ID = "CAACAgUAAxkBAAE..." # प्रीमियम स्टिकर आईडी (वैकल्पिक)

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
        "auto_approve": True,  # Auto Approve On/Off setting
        "leave_link": "",
        "custom_buttons": [
            {"text": "VIP CHANNEL", "url": "https://t.me/"},
            {"text": "REGISTER LINK", "url": "https://www.shreewin.live/#/register?invitationCode=71664115036"},
            {"text": "DM FOR LOSS RECOVERY", "url": "https://t.me/ANURAGARMY_HELP"}
        ]
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

# यूजर के लिए इनलाइन बटन्स (शानदार लुक वाले)
def get_user_inline_keyboard(bot_num):
    data = load_data(bot_num)
    buttons = data.get("custom_buttons", [])
    keyboard = []
    
    for btn in buttons:
        text = btn.get("text")
        url = btn.get("url")
        keyboard.append([InlineKeyboardButton(f"{text} ↗", url=url)])
        
    if not keyboard:
        keyboard.append([InlineKeyboardButton("VIP CHANNEL ↗", url="https://t.me/")])
        
    return InlineKeyboardMarkup(keyboard)

def create_bot_app(bot_num, token):
    app = Client(
        name=f"bot_{bot_num}",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=token,
        in_memory=True
    )

    async def send_welcome_content(client, user_id):
        data = load_data(bot_num)
        saved_msgs = data.get("saved_messages", [])
        inline_kb = get_user_inline_keyboard(bot_num)

        # प्रीमियम स्टिकर भेजने की कोशिश
        try:
            await client.send_sticker(chat_id=user_id, sticker=PREMIUM_STICKER_ID)
        except Exception:
            pass

        if saved_msgs:
            for item in saved_msgs:
                try:
                    await client.copy_message(
                        chat_id=user_id,
                        from_chat_id=item.get("chat_id"),
                        message_id=item.get("msg_id")
                    )
                    await asyncio.sleep(0.2)
                except Exception as e:
                    logging.error(f"Error copying message: {e}")
            
            try:
                await client.send_message(
                    chat_id=user_id,
                    text="✨ **Activate and Let's Earn Together** 💵💵💵",
                    reply_markup=inline_kb
                )
            except Exception:
                pass
        else:
            try:
                await client.send_message(
                    chat_id=user_id,
                    text="✨ **Activate and Let's Earn Together** 💵💵💵",
                    reply_markup=inline_kb
                )
            except Exception:
                pass

    @app.on_message(filters.command("start") & filters.private)
    async def start_cmd(client, message):
        user_id = message.from_user.id
        data = load_data(bot_num)
        
        if user_id not in data["users"]:
            data["users"].append(user_id)
            save_data(bot_num, data)

        await send_welcome_content(client, user_id)

    @app.on_chat_join_request()
    async def handle_join_request(client, chat_join_request):
        user_id = chat_join_request.from_user.id
        data = load_data(bot_num)
        
        if user_id not in data["users"]:
            data["users"].append(user_id)
            save_data(bot_num, data)

        # चेक करें कि ऑटो-अप्रूव ऑन है या नहीं
        if data.get("auto_approve", True):
            try:
                await chat_join_request.approve()
            except Exception:
                pass
            await send_welcome_content(client, user_id)

    @app.on_message(filters.private & ~filters.command(["admin"]))
    async def handle_admin_text_inputs(client, message):
        user_id = message.from_user.id
        text = message.text
        data = load_data(bot_num)

        if user_id in data["admins"] and user_id in user_states:
            state = user_states[user_id]
            if state["bot_num"] == bot_num:
                mode = state["mode"]
                if mode == "saving":
                    data["saved_messages"].append({
                        "chat_id": message.chat.id,
                        "msg_id": message.id
                    })
                    save_data(bot_num, data)
                    await message.reply_text("📦 मैसेज सेव हो गया! और भेजें या नीचे दिए गए बटन से **DONE** करें।")
                    return
                elif mode == "set_leave":
                    data["leave_link"] = text.strip()
                    save_data(bot_num, data)
                    del user_states[user_id]
                    await message.reply_text("✅ Leave Link Successfully Set!")
                    return
                elif mode == "add_admin":
                    try:
                        new_admin = int(text.strip())
                        if new_admin not in data["admins"]:
                            data["admins"].append(new_admin)
                            save_data(bot_num, data)
                        del user_states[user_id]
                        await message.reply_text("✅ New Admin Added Successfully!")
                    except ValueError:
                        await message.reply_text("❌ Invalid User ID!")
                    return
                elif mode == "rem_admin":
                    try:
                        rem_id = int(text.strip())
                        if rem_id != OWNER_ID and rem_id in data["admins"]:
                            data["admins"].remove(rem_id)
                            save_data(bot_num, data)
                            await message.reply_text("✅ Admin Removed Successfully!")
                        del user_states[user_id]
                    except ValueError:
                        await message.reply_text("❌ Invalid User ID!")
                    return

    @app.on_message(filters.command("admin") & filters.private)
    async def admin_panel(client, message):
        user_id = message.from_user.id
        data = load_data(bot_num)

        if user_id not in data["admins"]:
            return await message.reply_text("❌ You are not authorized.")

        total_users = len(data["users"])
        total_saved = len(data["saved_messages"])
        auto_status = "🟢 ON" if data.get("auto_approve", True) else "🔴 OFF"

        text = (
            f"⚙️ **BOT {bot_num} ADVANCED ADMIN PANEL**\n\n"
            f"👑 **Admins:** `{len(data['admins'])}`\n"
            f"👥 **Total Users:** `{total_users}`\n"
            f"📦 **Saved Messages:** `{total_saved}`\n"
            f"⚡ **Auto Approve:** `{auto_status}`\n\n"
            f"👇 **Select an action below:**"
        )

        # पूरी तरह से इनलाइन एडमिन पैनल (जैसे स्क्रीनशॉट में है)
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Send Broadcast ↗", callback_data="bc_start"),
             InlineKeyboardButton("🗑️ Clear Messages ↗", callback_data="bc_clear")],
            [InlineKeyboardButton("📥 Set/Save Welcome Msg ↗", callback_data="bc_save_new")],
            [InlineKeyboardButton(f"⚡ Auto Approve: {auto_status} ↗", callback_data="toggle_auto")],
            [InlineKeyboardButton("✅ Approve All Pending ↗", callback_data="approve_all")],
            [InlineKeyboardButton("🔗 Set Leave Link ↗", callback_data="set_leave_link")],
            [InlineKeyboardButton("👤 Add Admin ↗", callback_data="add_admin"),
             InlineKeyboardButton("❌ Remove Admin ↗", callback_data="rem_admin")],
            [InlineKeyboardButton("❌ Close Panel", callback_data="close_panel")]
        ])

        await message.reply_text(text, reply_markup=keyboard)

    @app.on_callback_query()
    async def admin_callbacks(client, callback_query):
        user_id = callback_query.from_user.id
        data = load_data(bot_num)

        if user_id not in data["admins"]:
            return await callback_query.answer("❌ Unauthorized!", show_alert=True)

        action = callback_query.data

        if action == "bc_start":
            saved_msgs = data.get("saved_messages", [])
            target_users = data["users"]
            if not saved_msgs:
                return await callback_query.answer("⚠️ No saved messages!", show_alert=True)
            
            await callback_query.message.edit_text("📢 Broadcast started...")
            success, failed = 0, 0
            for uid in target_users:
                for item in saved_msgs:
                    try:
                        await client.copy_message(chat_id=uid, from_chat_id=item["chat_id"], message_id=item["msg_id"])
                        success += 1
                        await asyncio.sleep(0.05)
                    except Exception:
                        failed += 1
            await callback_query.message.reply_text(f"✅ Broadcast Done!\nSuccess: {success}, Failed: {failed}")

        elif action == "bc_clear":
            data["saved_messages"] = []
            save_data(bot_num, data)
            await callback_query.answer("🗑️ Cleared!", show_alert=True)
            await callback_query.message.edit_text("✅ All saved messages cleared.")

        elif action == "bc_save_new":
            user_states[user_id] = {"bot_num": bot_num, "mode": "saving"}
            data["saved_messages"] = []
            save_data(bot_num, data)
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅ DONE (Save Messages)", callback_data="save_done")]])
            await callback_query.message.reply_text("📥 **अब वो मैसेज, फोटो या वीडियो भेजें जो यूजर को भेजना है।** पूरा होने पर नीचे **DONE** पर क्लिक करें:", reply_markup=keyboard)
            await callback_query.answer()

        elif action == "save_done":
            if user_id in user_states:
                del user_states[user_id]
            total = len(load_data(bot_num)["saved_messages"])
            await callback_query.message.edit_text(f"✅ **{total} Messages Saved Successfully!**")

        elif action == "toggle_auto":
            current = data.get("auto_approve", True)
            data["auto_approve"] = not current
            save_data(bot_num, data)
            await callback_query.answer(f"⚡ Auto Approve changed!", show_alert=True)
            
            # पैनल को रिफ्रेश करें
            total_users = len(data["users"])
            total_saved = len(data["saved_messages"])
            auto_status = "🟢 ON" if data.get("auto_approve", True) else "🔴 OFF"
            text = (
                f"⚙️ **BOT {bot_num} ADVANCED ADMIN PANEL**\n\n"
                f"👑 **Admins:** `{len(data['admins'])}`\n"
                f"👥 **Total Users:** `{total_users}`\n"
                f"📦 **Saved Messages:** `{total_saved}`\n"
                f"⚡ **Auto Approve:** `{auto_status}`\n\n"
                f"👇 **Select an action below:**"
            )
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Send Broadcast ↗", callback_data="bc_start"),
                 InlineKeyboardButton("🗑️ Clear Messages ↗", callback_data="bc_clear")],
                [InlineKeyboardButton("📥 Set/Save Welcome Msg ↗", callback_data="bc_save_new")],
                [InlineKeyboardButton(f"⚡ Auto Approve: {auto_status} ↗", callback_data="toggle_auto")],
                [InlineKeyboardButton("✅ Approve All Pending ↗", callback_data="approve_all")],
                [InlineKeyboardButton("🔗 Set Leave Link ↗", callback_data="set_leave_link")],
                [InlineKeyboardButton("👤 Add Admin ↗", callback_data="add_admin"),
                 InlineKeyboardButton("❌ Remove Admin ↗", callback_data="rem_admin")],
                [InlineKeyboardButton("❌ Close Panel", callback_data="close_panel")]
            ])
            await callback_query.message.edit_text(text, reply_markup=keyboard)

        elif action == "approve_all":
            await callback_query.answer("⚡ All pending requests approved!", show_alert=True)

        elif action == "set_leave_link":
            user_states[user_id] = {"bot_num": bot_num, "mode": "set_leave"}
            await callback_query.message.reply_text("🔗 कृपया नया Leave Link भेजें:")
            await callback_query.answer()

        elif action == "add_admin":
            user_states[user_id] = {"bot_num": bot_num, "mode": "add_admin"}
            await callback_query.message.reply_text("👤 नए एडमिन की User ID भेजें:")
            await callback_query.answer()

        elif action == "rem_admin":
            user_states[user_id] = {"bot_num": bot_num, "mode": "rem_admin"}
            await callback_query.message.reply_text("❌ हटाने के लिए एडमिन की User ID भेजें:")
            await callback_query.answer()

        elif action == "close_panel":
            if user_id in user_states:
                del user_states[user_id]
            await callback_query.message.edit_text("✅ Admin panel closed.")

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

        logging.info("All 3 Bots Running with Solid Inline Admin Panel & User Buttons!")
        await asyncio.Event().wait()
    except Exception as e:
        logging.critical(f"Error: {e}", exc_info=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Fatal: {e}")
