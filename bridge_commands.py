import asyncio
import time
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime

class BridgeCommands:
    def __init__(self, bot: Client, assistant_manager, audio_bridge, db):
        self.bot = bot
        self.assistant_manager = assistant_manager
        self.audio_bridge = audio_bridge
        self.db = db
        self.active_bridges = {}
        self.register_handlers()
    
    def register_handlers(self):
        
        @self.bot.on_message(filters.command("bridge") & filters.group)
        async def bridge_cmd(client, message: Message):
            if not self._is_sudo(message.from_user.id):
                return await message.reply("❌ Unauthorized!\nOnly sudo users can use this command.")
            
            if len(message.command) < 2:
                return await message.reply(
                    "**📖 Bridge Command Usage**\n\n"
                    "`/bridge TARGET_ID` - Start audio bridge\n"
                    "`/bridge TARGET_ID URL` - Bridge with custom audio source\n\n"
                    "**Examples:**\n"
                    "`/bridge -1001234567890`\n"
                    "`/bridge -1001234567890 https://radio.example.com/stream`\n\n"
                    "**Current Status:**\n"
                    f"• Assistants: `{self.assistant_manager.get_assistant_count()}`\n"
                    f"• Active Bridges: `{self.audio_bridge.get_bridge_count() if self.audio_bridge else 0}`"
                )
            
            status_msg = await message.reply("🎙️ **Starting audio bridge...**")
            
            try:
                source_id = message.chat.id
                target_input = message.command[1]
                audio_source = message.command[2] if len(message.command) > 2 else None
                
                # Validate source chat
                source_chat = await client.get_chat(source_id)
                source_name = source_chat.title or str(source_id)
                
                # Parse target ID
                target_id = await self._get_chat_id(target_input)
                if not target_id:
                    await status_msg.edit(f"❌ Target group not found: `{target_input}`")
                    return
                
                target_chat = await client.get_chat(target_id)
                target_name = target_chat.title or str(target_id)
                
                # Get assistant
                assistant = self.assistant_manager.get_assistant()
                if not assistant:
                    await status_msg.edit("❌ No assistant added! Use `/addstring` in private chat.")
                    return
                
                # Check membership
                await status_msg.edit(f"✅ Groups verified\n🎤 SOURCE: {source_name}\n🔊 TARGET: {target_name}")
                
                try:
                    await assistant['client'].get_chat_member(source_id, "me")
                except:
                    await status_msg.edit(f"❌ Assistant not in source group!\nAdd @{assistant['username']} to the group.")
                    return
                
                try:
                    await assistant['client'].get_chat_member(target_id, "me")
                except:
                    await status_msg.edit(f"❌ Assistant not in target group!\nAdd @{assistant['username']} to the target group.")
                    return
                
                # Start voice chats
                await status_msg.edit("🎤 Starting voice chats...")
                await self.assistant_manager.start_voice_chat(
                    list(self.assistant_manager.assistants.keys())[0], source_id
                )
                await self.assistant_manager.start_voice_chat(
                    list(self.assistant_manager.assistants.keys())[0], target_id
                )
                
                # Get current effects
                effects = self.audio_bridge.config if self.audio_bridge else {'gain': 100, 'echo': 0, 'loudness': 0, 'bass': 0}
                
                # Start bridge
                await status_msg.edit("🔊 Setting up audio bridge...")
                result = await self.audio_bridge.start_bridge(
                    source_id, target_id,
                    effects['gain'], effects['echo'],
                    effects['loudness'], effects['bass'],
                    audio_source
                )
                
                if result:
                    self.active_bridges[source_id] = {
                        'target_id': target_id,
                        'target_name': target_name,
                        'source_name': source_name,
                        'started_at': datetime.now()
                    }
                    
                    # Save to database
                    self.db.save_bridge(
                        source_id, target_id, source_name, target_name,
                        effects['gain'], effects['echo'], effects['loudness'], effects['bass']
                    )
                    
                    # Create inline keyboard
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("🎛️ Effects", callback_data="effects"),
                         InlineKeyboardButton("🛑 Stop", callback_data="stop")],
                        [InlineKeyboardButton("📊 Status", callback_data="status")]
                    ])
                    
                    await status_msg.edit(
                        f"**✅ AUDIO BRIDGE ACTIVE!**\n\n"
                        f"🎤 **SOURCE:** {source_name}\n"
                        f"🔊 **TARGET:** {target_name}\n"
                        f"🎛️ **EFFECTS:**\n"
                        f"• Gain: `{effects['gain']}%`\n"
                        f"• Echo: `{effects['echo']}%`\n"
                        f"• Loudness: `{effects['loudness']}%`\n"
                        f"• Bass: `{effects['bass']}%`\n\n"
                        f"**Audio is now being forwarded live!**",
                        reply_markup=keyboard
                    )
                else:
                    await status_msg.edit("❌ Failed to start bridge!")
                    
            except Exception as e:
                await status_msg.edit(f"❌ Error: `{str(e)[:150]}`")
        
        @self.bot.on_message(filters.command("stop") & filters.group)
        async def stop_cmd(client, message: Message):
            if not self._is_sudo(message.from_user.id):
                return await message.reply("❌ Unauthorized!")
            
            source_id = message.chat.id
            if source_id in self.active_bridges:
                await self.audio_bridge.stop_bridge(source_id)
                self.db.close_bridge(source_id, self.active_bridges[source_id]['target_id'])
                del self.active_bridges[source_id]
                await message.reply("✅ **Bridge stopped successfully!**")
            else:
                await message.reply("❌ No active bridge in this group!")
        
        @self.bot.on_message(filters.command("stopall"))
        async def stopall_cmd(client, message: Message):
            if not self._is_sudo(message.from_user.id):
                return await message.reply("❌ Unauthorized!")
            
            status_msg = await message.reply("🛑 Stopping all bridges...")
            count = await self.audio_bridge.stop_all_bridges()
            self.active_bridges.clear()
            await status_msg.edit(f"✅ Stopped `{count}` active bridges!")
        
        @self.bot.on_message(filters.command("bridges"))
        async def list_bridges_cmd(client, message: Message):
            if not self._is_sudo(message.from_user.id):
                return await message.reply("❌ Unauthorized!")
            
            if not self.active_bridges:
                return await message.reply("❌ No active bridges!")
            
            text = "**🌉 Active Bridges**\n\n"
            for source_id, bridge in self.active_bridges.items():
                text += f"• Source: `{bridge['source_name']}`\n"
                text += f"  Target: `{bridge['target_name']}`\n"
                text += f"  Started: `{bridge['started_at'].strftime('%H:%M:%S')}`\n\n"
            
            await message.reply(text)
    
    async def _get_chat_id(self, chat_input: str):
        """Convert various chat identifier formats to chat ID"""
        try:
            if chat_input.startswith('@'):
                chat = await self.bot.get_chat(chat_input)
                return chat.id
            elif chat_input.isdigit() or (chat_input.startswith('-') and chat_input[1:].isdigit()):
                return int(chat_input)
            elif 't.me/' in chat_input:
                username = chat_input.split('t.me/')[-1].split('/')[0]
                chat = await self.bot.get_chat(f"@{username}")
                return chat.id
        except Exception:
            return None
        return None
    
    def _is_sudo(self, user_id: int) -> bool:
        from config.settings import SUDO_USERS
        return user_id in SUDO_USERS