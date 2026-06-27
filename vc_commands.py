import os
import subprocess
import asyncio
import time
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.raw.functions.phone import LeaveGroupCall, CreateGroupCall
from pyrogram.raw.types import InputGroupCall

class VCCommands:
    def __init__(self, bot: Client, assistant_manager, audio_bridge, screenshare_manager):
        self.bot = bot
        self.assistant_manager = assistant_manager
        self.audio_bridge = audio_bridge
        self.screenshare_manager = screenshare_manager
        self.register_handlers()
    
    def register_handlers(self):
        
        @self.bot.on_message(filters.command("leavevc") & filters.group)
        async def leave_vc_cmd(client, message: Message):
            if not self._is_sudo(message.from_user.id):
                return await message.reply("❌ Unauthorized!")
            
            chat_id = message.chat.id
            status_msg = await message.reply("🎤 **Leaving voice chat...**")
            
            try:
                assistant = self.assistant_manager.get_assistant()
                if not assistant:
                    return await status_msg.edit("❌ No assistant found!")
                
                # Method 1: Use PyTgCalls
                if self.audio_bridge:
                    if chat_id in self.audio_bridge.active_bridges:
                        await self.audio_bridge.stop_bridge(chat_id)
                    elif chat_id in self.audio_bridge.calls:
                        await self.audio_bridge.client.leave_group_call(chat_id)
                    else:
                        # Method 2: Use raw API
                        try:
                            full_chat = await assistant['client'].get_chat(chat_id)
                            if hasattr(full_chat, 'call') and full_chat.call:
                                await assistant['client'].invoke(
                                    LeaveGroupCall(
                                        call=InputGroupCall(
                                            id=full_chat.call.id,
                                            access_hash=full_chat.call.access_hash
                                        ),
                                        source=0
                                    )
                                )
                        except:
                            pass
                
                await status_msg.edit("✅ **Left voice chat successfully!**")
                
            except Exception as e:
                await status_msg.edit(f"❌ Failed to leave: `{str(e)[:100]}`")
        
        @self.bot.on_message(filters.command("joinvc") & filters.group)
        async def join_vc_cmd(client, message: Message):
            if not self._is_sudo(message.from_user.id):
                return await message.reply("❌ Unauthorized!")
            
            chat_id = message.chat.id
            status_msg = await message.reply("🎤 **Joining voice chat...**")
            
            try:
                assistant = self.assistant_manager.get_assistant()
                if not assistant:
                    return await status_msg.edit("❌ No assistant found!")
                
                # Start voice chat if not exists
                try:
                    peer = await assistant['client'].resolve_peer(chat_id)
                    await assistant['client'].invoke(
                        CreateGroupCall(
                            peer=peer,
                            random_id=int(time.time() * 1000) % 1000000
                        )
                    )
                    await asyncio.sleep(2)
                except Exception:
                    pass  # Voice chat may already exist
                
                await status_msg.edit("✅ **Joined voice chat successfully!**")
                
            except Exception as e:
                await status_msg.edit(f"❌ Failed to join: `{str(e)[:100]}`")
        
        @self.bot.on_message(filters.command("screenshare") & filters.group)
        async def screenshare_cmd(client, message: Message):
            if not self._is_sudo(message.from_user.id):
                return await message.reply("❌ Unauthorized!")
            
            status_msg = await message.reply("🖥️ **Starting screenshare...**")
            
            chat_id = message.chat.id
            quality = message.command[1] if len(message.command) > 1 else "720p"
            fps = int(message.command[2]) if len(message.command) > 2 else 30
            
            try:
                assistant = self.assistant_manager.get_assistant()
                if not assistant:
                    return await status_msg.edit("❌ No assistant found!")
                
                # Take screenshot for preview
                preview_path = await self._take_screenshot()
                
                # Start screenshare
                result = await self.screenshare_manager.start_screenshare(
                    chat_id, 
                    assistant['bridge'],
                    quality,
                    fps
                )
                
                if result:
                    # Send preview image
                    if preview_path and os.path.exists(preview_path):
                        await message.reply_photo(
                            preview_path,
                            caption=f"**🖥️ Screenshare Active!**\n\n"
                                   f"• Quality: `{quality}`\n"
                                   f"• FPS: `{fps}`\n"
                                   f"• Started: Just now\n\n"
                                   f"Use `/screenshareoff` to stop sharing."
                        )
                    else:
                        await status_msg.edit(
                            f"**✅ Screenshare Active!**\n\n"
                            f"• Quality: `{quality}`\n"
                            f"• FPS: `{fps}`\n\n"
                            f"Use `/screenshareoff` to stop."
                        )
                    
                    # Delete status message
                    await status_msg.delete()
                else:
                    await status_msg.edit("❌ Failed to start screenshare!")
                    
            except Exception as e:
                await status_msg.edit(f"❌ Error: `{str(e)[:100]}`")
        
        @self.bot.on_message(filters.command("screenshareoff") & filters.group)
        async def screenshare_off_cmd(client, message: Message):
            if not self._is_sudo(message.from_user.id):
                return await message.reply("❌ Unauthorized!")
            
            chat_id = message.chat.id
            status_msg = await message.reply("🛑 **Stopping screenshare...**")
            
            try:
                result = await self.screenshare_manager.stop_screenshare(chat_id)
                
                if result:
                    await status_msg.edit("✅ **Screenshare stopped successfully!**")
                else:
                    await status_msg.edit("❌ No active screenshare found!")
                    
            except Exception as e:
                await status_msg.edit(f"❌ Error: `{str(e)[:100]}`")
        
        @self.bot.on_message(filters.command("vcstatus"))
        async def vc_status_cmd(client, message: Message):
            chat_id = message.chat.id
            
            try:
                assistant = self.assistant_manager.get_assistant()
                if not assistant:
                    return await message.reply("❌ No assistant found!")
                
                # Check voice chat status
                is_in_vc = False
                if self.audio_bridge:
                    is_in_vc = chat_id in self.audio_bridge.active_bridges
                
                is_screenshare = self.screenshare_manager.is_active(chat_id)
                
                # Get member count
                member_count = "Unknown"
                try:
                    full_chat = await assistant['client'].get_chat(chat_id)
                    if hasattr(full_chat, 'call') and full_chat.call:
                        member_count = "Active"
                except:
                    pass
                
                status_text = f"""
**🎙️ Voice Chat Status**

┌─────────────────────────────┐
│ **Chat ID:** `{chat_id}`       │
│ **In Voice Chat:** `{'✅ Yes' if is_in_vc else '❌ No'}` │
│ **Screenshare:** `{'✅ Active' if is_screenshare else '❌ Inactive'}` │
│ **Status:** `🎤 Live`              │
└─────────────────────────────┘

**Commands:**
• `/leavevc` - Leave this chat
• `/screenshare` - Start screenshare
• `/screenshareoff` - Stop screenshare
"""
                await message.reply(status_text)
                
            except Exception as e:
                await message.reply(f"❌ Error: `{str(e)[:100]}`")
    
    async def _take_screenshot(self) -> str:
        """Take screenshot for preview"""
        try:
            screenshot_path = "/tmp/screenshare_preview.png"
            
            if subprocess.call(['which', 'scrot'], stdout=subprocess.DEVNULL) == 0:
                subprocess.call(['scrot', screenshot_path])
            elif subprocess.call(['which', 'import'], stdout=subprocess.DEVNULL) == 0:
                subprocess.call(['import', '-window', 'root', screenshot_path])
            else:
                return None
            
            return screenshot_path if os.path.exists(screenshot_path) else None
        except:
            return None
    
    def _is_sudo(self, user_id: int) -> bool:
        from config.settings import SUDO_USERS
        return user_id in SUDO_USERS