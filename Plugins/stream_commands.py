import os
import subprocess
import asyncio
from pathlib import Path
from pyrogram import Client, filters
from pyrogram.types import Message

class StreamCommands:
    def __init__(self, bot: Client, assistant_manager, audio_bridge):
        self.bot = bot
        self.assistant_manager = assistant_manager
        self.audio_bridge = audio_bridge
        self.download_tasks = {}
        self.register_handlers()
    
    def register_handlers(self):
        
        @self.bot.on_message(filters.command("radio") & filters.group)
        async def radio_cmd(client, message: Message):
            if not self._is_sudo(message.from_user.id):
                return await message.reply("❌ Unauthorized!")
            
            if len(message.command) < 2:
                return await message.reply(
                    "**📻 Radio Command**\n\n"
                    "Usage: `/radio RADIO_URL`\n\n"
                    "**Example:**\n"
                    "`/radio https://ice1.somafm.com/groovesalad-128-mp3`\n\n"
                    "**Popular Radio Streams:**\n"
                    "• Groove Salad: `https://ice1.somafm.com/groovesalad-128-mp3`\n"
                    "• Radio Paradise: `https://stream-uk1.radioparadise.com/mp3-128`\n"
                    "• Classic Rock: `https://stream.laut.fm/classicrock`"
                )
            
            status_msg = await message.reply("📻 **Switching radio stream...**")
            
            try:
                radio_url = message.command[1]
                
                if message.chat.id in self.audio_bridge.active_bridges:
                    # Update existing bridge
                    bridge = self.audio_bridge.active_bridges[message.chat.id]
                    await self.audio_bridge.stop_bridge(message.chat.id)
                    
                    await self.audio_bridge.start_bridge(
                        message.chat.id, bridge['target_id'],
                        bridge['gain'], bridge['echo'],
                        bridge['loudness'], bridge['bass'],
                        radio_url
                    )
                    
                    await status_msg.edit(f"✅ **Radio stream changed!**\n\nNow playing: `{radio_url}`")
                else:
                    # Start new stream in current group
                    assistant = self.assistant_manager.get_assistant()
                    if assistant:
                        await self.assistant_manager.start_voice_chat(
                            list(self.assistant_manager.assistants.keys())[0], message.chat.id
                        )
                        
                        await self.audio_bridge.start_bridge(
                            message.chat.id, message.chat.id,
                            100, 0, 0, 0, radio_url
                        )
                        
                        await status_msg.edit(f"✅ **Radio streaming started!**\n\nNow playing: `{radio_url}`")
                    else:
                        await status_msg.edit("❌ No assistant found!")
                        
            except Exception as e:
                await status_msg.edit(f"❌ Error: `{str(e)[:100]}`")
        
        @self.bot.on_message(filters.command("yt") & filters.group)
        async def youtube_cmd(client, message: Message):
            if not self._is_sudo(message.from_user.id):
                return await message.reply("❌ Unauthorized!")
            
            if len(message.command) < 2:
                return await message.reply("Usage: `/yt YOUTUBE_URL`\n\nExample: `/yt https://youtube.com/watch?v=dQw4w9WgXcQ`")
            
            url = message.command[1]
            status_msg = await message.reply("🎵 **Downloading YouTube audio...**")
            
            try:
                # Download YouTube audio
                file_path = await self._download_youtube_audio(url, message.chat.id)
                
                if not file_path:
                    await status_msg.edit("❌ Failed to download audio!")
                    return
                
                await status_msg.edit("✅ Downloaded! Now streaming...")
                
                if message.chat.id in self.audio_bridge.active_bridges:
                    # Update existing bridge with local file
                    bridge = self.audio_bridge.active_bridges[message.chat.id]
                    await self.audio_bridge.stop_bridge(message.chat.id)
                    
                    await self.audio_bridge.start_bridge(
                        message.chat.id, bridge['target_id'],
                        bridge['gain'], bridge['echo'],
                        bridge['loudness'], bridge['bass'],
                        file_path
                    )
                    
                    await status_msg.edit("✅ **YouTube audio is now playing in the bridge!**")
                else:
                    # Start direct stream
                    assistant = self.assistant_manager.get_assistant()
                    if assistant:
                        await self.assistant_manager.start_voice_chat(
                            list(self.assistant_manager.assistants.keys())[0], message.chat.id
                        )
                        
                        await self.audio_bridge.start_bridge(
                            message.chat.id, message.chat.id,
                            100, 0, 0, 0, file_path
                        )
                        
                        await status_msg.edit("✅ **YouTube audio is now playing!**")
                    else:
                        await status_msg.edit("❌ No assistant found!")
                        
            except Exception as e:
                await status_msg.edit(f"❌ Error: `{str(e)[:100]}`")
        
        @self.bot.on_message(filters.command("play") & filters.group)
        async def play_cmd(client, message: Message):
            if not self._is_sudo(message.from_user.id):
                return await message.reply("❌ Unauthorized!")
            
            if not message.reply_to_message or not message.reply_to_message.audio:
                return await message.reply("Reply to an audio file with `/play` to play it!")
            
            status_msg = await message.reply("🎵 **Playing audio file...**")
            
            try:
                # Download replied audio
                audio = message.reply_to_message.audio
                file_path = await message.reply_to_message.download()
                
                if not file_path:
                    await status_msg.edit("❌ Failed to download audio!")
                    return
                
                if message.chat.id in self.audio_bridge.active_bridges:
                    bridge = self.audio_bridge.active_bridges[message.chat.id]
                    await self.audio_bridge.stop_bridge(message.chat.id)
                    
                    await self.audio_bridge.start_bridge(
                        message.chat.id, bridge['target_id'],
                        bridge['gain'], bridge['echo'],
                        bridge['loudness'], bridge['bass'],
                        file_path
                    )
                    
                    await status_msg.edit(f"✅ **Now playing:** `{audio.file_name}`")
                else:
                    assistant = self.assistant_manager.get_assistant()
                    if assistant:
                        await self.assistant_manager.start_voice_chat(
                            list(self.assistant_manager.assistants.keys())[0], message.chat.id
                        )
                        
                        await self.audio_bridge.start_bridge(
                            message.chat.id, message.chat.id,
                            100, 0, 0, 0, file_path
                        )
                        
                        await status_msg.edit(f"✅ **Now playing:** `{audio.file_name}`")
                    else:
                        await status_msg.edit("❌ No assistant found!")
                        
            except Exception as e:
                await status_msg.edit(f"❌ Error: `{str(e)[:100]}`")
    
    async def _download_youtube_audio(self, url: str, chat_id: int) -> str:
        """Download YouTube audio using yt-dlp"""
        try:
            from yt_dlp import YoutubeDL
            
            download_path = f"downloads/yt_{chat_id}_{int(asyncio.get_event_loop().time())}.mp3"
            Path("downloads").mkdir(exist_ok=True)
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': download_path.replace('.mp3', '.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True,
                'no_warnings': True,
            }
            
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                filename = filename.replace('.webm', '.mp3').replace('.m4a', '.mp3')
                
                return filename
                
        except Exception as e:
            print(f"Download error: {e}")
            return None
    
    def _is_sudo(self, user_id: int) -> bool:
        from config.settings import SUDO_USERS
        return user_id in SUDO_USERS