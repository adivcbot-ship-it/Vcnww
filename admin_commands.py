import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

class AdminCommands:
    def __init__(self, bot: Client, assistant_manager, db, audio_bridge):
        self.bot = bot
        self.assistant_manager = assistant_manager
        self.db = db
        self.audio_bridge = audio_bridge
        self.register_handlers()
    
    def register_handlers(self):
        
        @self.bot.on_message(filters.command("addstring") & filters.private)
        async def add_string_cmd(client, message: Message):
            if not self._is_sudo(message.from_user.id):
                return await message.reply("❌ Unauthorized! Only sudo users can add assistants.")
            
            if len(message.command) < 2:
                return await message.reply(
                    "**📖 Add Assistant Command**\n\n"
                    "Usage: `/addstring SESSION_STRING`\n\n"
                    "**How to get session string:**\n"
                    "1. Go to @StringSessionBot on Telegram\n"
                    "2. Send `/start`\n"
                    "3. Send your phone number (with country code)\n"
                    "4. Copy the session string you receive\n\n"
                    "**Example:**\n"
                    "`/addstring AQGj8Mk...`"
                )
            
            session_string = message.text.split(None, 1)[1]
            status_msg = await message.reply("⏳ **Adding assistant...**")
            
            try:
                result = await self.assistant_manager.add_assistant(session_string)
                
                if result:
                    assistant = self.assistant_manager.get_assistant()
                    
                    # Save to database
                    self.db.save_assistant(
                        session_string,
                        assistant['name'],
                        assistant['user_id'],
                        assistant.get('username')
                    )
                    
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("📊 Status", callback_data="status"),
                         InlineKeyboardButton("❌ Remove", callback_data="remove_assistant")]
                    ])
                    
                    await status_msg.edit(
                        f"✅ **Assistant Added Successfully!**\n\n"
                        f"**Name:** {assistant['name']}\n"
                        f"**Username:** @{assistant.get('username', 'N/A')}\n"
                        f"**User ID:** `{assistant['user_id']}`\n\n"
                        f"**Next Steps:**\n"
                        f"1. Add @{assistant.get('username', 'assistant')} to both groups\n"
                        f"2. Make the assistant an admin\n"
                        f"3. Use `/bridge TARGET_ID` in the source group",
                        reply_markup=keyboard
                    )
                else:
                    await status_msg.edit("❌ Failed to add assistant! Invalid session string.")
                    
            except Exception as e:
                await status_msg.edit(f"❌ Error: `{str(e)[:150]}`")
        
        @self.bot.on_message(filters.command("removeassistant") & filters.private)
        async def remove_assistant_cmd(client, message: Message):
            if not self._is_sudo(message.from_user.id):
                return await message.reply("❌ Unauthorized!")
            
            if self.assistant_manager.get_assistant_count() == 0:
                return await message.reply("❌ No assistants to remove!")
            
            status_msg = await message.reply("⏳ Removing assistant...")
            
            session_string = list(self.assistant_manager.assistants.keys())[0]
            await self.assistant_manager.remove_assistant(session_string)
            self.db.remove_assistant(session_string)
            
            await status_msg.edit("✅ Assistant removed successfully!")
        
        @self.bot.on_message(filters.command("assistants") & filters.private)
        async def list_assistants_cmd(client, message: Message):
            if not self._is_sudo(message.from_user.id):
                return await message.reply("❌ Unauthorized!")
            
            assistants = self.assistant_manager.get_all_assistants()
            
            if not assistants:
                return await message.reply("❌ No assistants found!\nUse `/addstring` to add one.")
            
            text = "**🤖 Active Assistants**\n\n"
            for i, ass in enumerate(assistants, 1):
                text += f"{i}. **{ass['name']}**\n"
                text += f"   • Username: @{ass.get('username', 'N/A')}\n"
                text += f"   • User ID: `{ass['user_id']}`\n\n"
            
            await message.reply(text)
        
        @self.bot.on_message(filters.command("broadcast") & filters.private)
        async def broadcast_cmd(client, message: Message):
            if not self._is_sudo(message.from_user.id):
                return await message.reply("❌ Unauthorized!")
            
            if len(message.command) < 2:
                return await message.reply("Usage: `/broadcast MESSAGE`")
            
            broadcast_text = message.text.split(None, 1)[1]
            status_msg = await message.reply("📢 Broadcasting message...")
            
            count = 0
            for ass in self.assistant_manager.get_all_assistants():
                try:
                    await ass['client'].send_message("me", f"📢 **Broadcast**\n\n{broadcast_text}")
                    count += 1
                except:
                    pass
            
            await status_msg.edit(f"✅ Broadcast sent to {count} assistants!")
        
        @self.bot.on_message(filters.command("restart") & filters.private)
        async def restart_cmd(client, message: Message):
            if not self._is_sudo(message.from_user.id):
                return await message.reply("❌ Unauthorized!")
            
            await message.reply("🔄 Restarting bot...")
            
            # Cleanup
            if self.audio_bridge:
                await self.audio_bridge.stop_all_bridges()
            
            # Restart
            import sys
            import os
            os.execv(sys.executable, [sys.executable] + sys.argv)
        
        @self.bot.on_message(filters.command("logs") & filters.private)
        async def logs_cmd(client, message: Message):
            if not self._is_sudo(message.from_user.id):
                return await message.reply("❌ Unauthorized!")
            
            try:
                with open('logs/vcfight.log', 'r') as f:
                    logs = f.read()[-3000:]  # Last 3000 characters
                
                # Split into multiple messages if too long
                if len(logs) > 4000:
                    for i in range(0, len(logs), 4000):
                        await message.reply(f"```{logs[i:i+4000]}```")
                else:
                    await message.reply(f"```{logs}```")
            except Exception as e:
                await message.reply(f"❌ Failed to read logs: {e}")
    
    def _is_sudo(self, user_id: int) -> bool:
        from config.settings import SUDO_USERS
        return user_id in SUDO_USERS