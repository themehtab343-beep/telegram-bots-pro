import os
import json
import logging
import asyncio
from aiohttp import web
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    ReplyKeyboardMarkup, 
    KeyboardButton,
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
        "leave_link": "",
        "custom_buttons": [
            {"text": "🟥 Get The Number Sureshot Hack", "url": "https://t.me/"},
            {"text": "🟩 Shreewin Official Link", "url": "https://www.shreewin.live/#/register?invitationCode=71664115036"},
            {"text": "🟦 Contact Official Customer Support", "url": "https://t.me/ANURAGARMY_HELP"}
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

def get_dynamic_reply_keyboard(bot_num):
    data = load_data(bot_num)
    buttons = data.get("custom_buttons", [])
    keyboard_rows = []
    
    colors = ["🟥 ", "🟩 ", "🟦 ", "🟨 ", "🟪 "]
    
    for idx, btn in enumerate(buttons):
        text = btn.get("text")
        if not any(text.startswith(c) for c in ["🟥", "🟩", "🟦", "🟨", "🟪", "🔴", "🟢", "🔵"]):
            color_prefix = colors[idx % len(colors)]
            text = f"{color_prefix}{text}"
            
        keyboard_rows.append([KeyboardButton(text)])
    
    if not keyboard_rows:
        keyboard_rows = [[KeyboardButton("🟥 Get The Number Sureshot Hack")]]
        
    return ReplyKeyboardMarkup(keyboard_rows, resize_keyboard=True)

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
        reply_kb = get_dynamic_reply_keyboard(bot_num)

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
                    logging.error(f"Error copying saved message: {e}")
            
            try:
                await client.send_message(
                    chat_id=user_id,
                    text="🎛️ **Menu — Tap a button below to get the content**",
                    reply_markup=reply_kb
                )
            except Exception:
                pass
        else:
            try:
                await client.send_message(
                    chat_id=user_id,
                    text="✨ **WELCOME TO VIP PANEL** ✨\nTap an option below:",
                    reply_markup=reply_kb
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

        try:
            await chat_join_request.approve()
        except Exception:
            pass
        await send_welcome_content(client, user_id)

    @app.on_message(filters.private & ~filters.command(["admin"]))
    async def handle_text_inputs(client, message):
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
                    await message.reply_text(f"📦 Message # {len(data['saved_messages'])} received! और भेजें या नीचे DONE पर क्लिक करें।")
                    return
                elif mode == "add_btn_name":
                    state["btn_text"] = text.strip()
                    state["mode"] = "add_btn_link"
                    await message.reply_text("🔗 अब इस बटन का **Link (URL)** या रिस्पांस टेक्स्ट भेजें:")
                    return
                elif mode == "add_btn_link":
                    btn_text = state.get("btn_text")
                    btn_url = text.strip()
                    data["custom_buttons"].append({"text": btn_text, "url": btn_url})
                    save_data(bot_num, data)
                    del user_states[user_id]
                    await message.reply_text(f"✅ नया कलरफुल बटन जोड़ दिया गया!\n\nनाम: {btn_text}\nलिंक: {btn_url}")
                    return
                elif mode == "add_admin":
                    try:
                        new_admin = int(text.strip())
                        if new_admin not in data["admins"]:
                            data["admins"].append(new_admin)
                            save_data(bot_num, data)
                        del user_states[user_id]
                        await message.reply_text(f"✅ Admin added successfully!")
                    except ValueError:
                        await message.reply_text("❌ Invalid ID!")
                    return
                elif mode == "rem_admin":
                    try:
                        rem_id = int(text.strip())
                        if rem_id != OWNER_ID and rem_id in data["admins"]:
                            data["admins"].remove(rem_id)
                            save_data(bot_num, data)
                            await message.reply_text(f"✅ Admin removed!")
                        del user_states[user_id]
                    except ValueError:
                        await message.reply_text("❌ Invalid ID!")
                    return

        buttons = data.get("custom_buttons", [])
        matched = False
        for btn in buttons:
            btn_raw_text = btn.get("text")
            if text.endswith(btn_raw_text.replace("🟥 ", "").replace("🟩 ", "").replace("🟦 ", "").replace("🟨 ", "").replace("🟪 ", "")) or text == btn_raw_text:
                matched = True
                url = btn.get("url", "")
                if url.startswith("http"):
                    await message.reply_text(f"🔗 **Official Link:**\n{url}", reply_markup=get_dynamic_reply_keyboard(bot_num))
                else:
                    await message.reply_text(f"📌 {url}", reply_markup=get_dynamic_reply_keyboard(bot_num))
                break

        if not matched and user_id not in data["admins"]:
            await message.reply_text("✨ Tap a button below:", reply_markup=get_dynamic_reply_keyboard(bot_num))

    @app.on_message(filters.command("admin") & filters.private)
    async def admin_panel(client, message):
        user_id = message.from_user.id
        data = load_data(bot_num)

        if user_id not in data["admins"]:
            return await message.reply_text("❌ You are not authorized.")

        total_users = len(data["users"])
        total_saved = len(data["saved_messages"])
        total_btns = len(data.get("custom_buttons", []))

        text = (
            f"⚙️ **BOT {bot_num} ADVANCED ADMIN PANEL**\n\n"
            f"👑 **Admins:** `{len(data['admins'])}`\n"
            f"👥 **Total Joined Users:** `{total_users}`\n"
            f"📦 **Saved Messages:** `{total_saved}`\n"
            f"🎛️ **Menu Buttons:** `{total_btns}`"
        )

        # आपके स्क्रीनशॉट वाले बिल्कुल सटीक नीले, हरे और लाल रंग के इनलाइन बटन्स
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Send Broadcast", callback_data="bc_start"),
             InlineKeyboardButton("🗑️ Clear Messages", callback_data="bc_clear")],
            [InlineKeyboardButton("🟩 Save New Messages", callback_data="bc_save_new")],
            [InlineKeyboardButton("🟦 Add Menu Button", callback_data="btn_add"),
             InlineKeyboardButton("🟥 Manage/Remove Buttons", callback_data="btn_manage")],
            [InlineKeyboardButton("🟩 Approve All Requests", callback_data="approve_all")],
            [InlineKeyboardButton("🟦 Add Admin", callback_data="add_admin"),
             InlineKeyboardButton("🟥 Remove Admin", callback_data="rem_admin")]
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
            keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅ DONE", callback_data="save_done")]])
            await callback_query.message.reply_text("📥 **Send setup videos, APK or messages to save.** Click DONE when finished:", reply_markup=keyboard)
            await callback_query.answer()

        elif action == "save_done":
            if user_id in user_states:
                del user_states[user_id]
            total = len(load_data(bot_num)["saved_messages"])
            await callback_query.message.edit_text(f"✅ **{total} Messages Saved Successfully!**")

        elif action == "btn_add":
            user_states[user_id] = {"bot_num": bot_num, "mode": "add_btn_name"}
            await callback_query.message.reply_text("➕ नए कलरफुल कीबोर्ड बटन का **नाम (Text)** भेजें:")
            await callback_query.answer()

        elif action == "btn_manage":
            buttons = data.get("custom_buttons", [])
            if not buttons:
                return await callback_query.answer("⚠️ कोई बटन मौजूद नहीं है!", show_alert=True)
            
            btn_kb = []
            for idx, b in enumerate(buttons):
                btn_kb.append([InlineKeyboardButton(f"❌ Remove: {b['text']}", callback_data=f"del_btn_{idx}")])
            btn_kb.append([InlineKeyboardButton("🗑️ Remove All Buttons", callback_data="del_all_btns")])
            
            await callback_query.message.edit_text("🎛️ **Manage Menu Buttons:**\nनीचे दिए गए बटन्स में से जिसे हटाना हो उसपर क्लिक करें:", reply_markup=InlineKeyboardMarkup(btn_kb))
            await callback_query.answer()

        elif action.startswith("del_btn_"):
            idx = int(action.split("_")[2])
            buttons = data.get("custom_buttons", [])
            if idx < len(buttons):
                removed = buttons.pop(idx)
                save_data(bot_num, data)
                await callback_query.answer(f"✅ हटाया गया: {removed['text']}", show_alert=True)
                await callback_query.message.edit_text("✅ बटन हटा दिया गया है। /admin कमांड से दोबारा पैनल खोलें।")

        elif action == "del_all_btns":
            data["custom_buttons"] = []
            save_data(bot_num, data)
            await callback_query.answer("🗑️ सारे बटन्स डिलीट कर दिए गए!", show_alert=True)
            await callback_query.message.edit_text("✅ सभी मेनू बटन्स साफ कर दिए गए हैं।")

        elif action == "approve_all":
            await callback_query.answer("⚡ चैनल ज्वाइन रिक्वेस्ट ऑटो-अप्रूव हो रही हैं!", show_alert=True)

        elif action == "add_admin":
            user_states[user_id] = {"bot_num": bot_num, "mode": "add_admin"}
            await callback_query.message.reply_text("➕ Send User ID to add admin:")
            await callback_query.answer()

        elif action == "rem_admin":
            user_states[user_id] = {"bot_num": bot_num, "mode": "rem_admin"}
            await callback_query.message.reply_text("➖ Send User ID to remove admin:")
            await callback_query.answer()

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

        logging.info("All 3 Bots Running with Colored Inline & Reply Buttons!")
        await asyncio.Event().wait()
    except Exception as e:
        logging.critical(f"Error: {e}", exc_info=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Fatal: {e}")
