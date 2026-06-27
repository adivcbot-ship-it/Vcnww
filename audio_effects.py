import json
from pathlib import Path
from pyrogram import Client, filters
from pyrogram.types import Message
from core.effects import AudioEffects

class AudioEffectsCommands:
    def __init__(self, bot: Client, audio_bridge, config, assistant_manager):
        self.bot = bot
        self.audio_bridge = audio_bridge
        self.config = config
        self.assistant_manager = assistant_manager
        self.register_handlers()
    
    def register_handlers(self):
        
        @self.bot.on_message(filters.command("gain") & filters.group)
        async def gain_cmd(client, message: Message):
            if not self._is_sudo(message.from_user.id):
                return await message.reply("❌ Unauthorized!")
            
            if len(message.command) < 2:
                current = self.config.get('gain', 100)
                return await message.reply(f"📊 **Current Gain:** `{current}%`\n\nRange: 0-500%\nUsage: `/gain 150`")
            
            try:
                gain = float(message.command[1])
                if AudioEffects.validate_value(gain, 0, 500):
                    self.config['gain'] = gain
                    await self._save_config()
                    
                    if message.chat.id in self.audio_bridge.active_bridges:
                        await self.audio_bridge.update_effects(message.chat.id, gain=gain)
                    
                    # Visual feedback
                    bar = self._create_visual_bar(gain, 500, 20)
                    await message.reply(f"✅ **Gain: `{gain}%`**\n\n{bar}")
                else:
                    await message.reply("❌ Gain must be between 0 and 500!")
            except ValueError:
                await message.reply("❌ Invalid value! Please enter a number.")
        
        @self.bot.on_message(filters.command("echo") & filters.group)
        async def echo_cmd(client, message: Message):
            if not self._is_sudo(message.from_user.id):
                return await message.reply("❌ Unauthorized!")
            
            if len(message.command) < 2:
                current = self.config.get('echo', 0)
                return await message.reply(f"📊 **Current Echo:** `{current}%`\n\nRange: 0-100%\nUsage: `/echo 50`")
            
            try:
                echo = float(message.command[1])
                if AudioEffects.validate_value(echo, 0, 100):
                    self.config['echo'] = echo
                    await self._save_config()
                    
                    if message.chat.id in self.audio_bridge.active_bridges:
                        await self.audio_bridge.update_effects(message.chat.id, echo=echo)
                    
                    bar = self._create_visual_bar(echo, 100, 20)
                    await message.reply(f"✅ **Echo: `{echo}%`**\n\n{bar}")
                else:
                    await message.reply("❌ Echo must be between 0 and 100!")
            except ValueError:
                await message.reply("❌ Invalid value!")
        
        @self.bot.on_message(filters.command("loudness") & filters.group)
        async def loudness_cmd(client, message: Message):
            if not self._is_sudo(message.from_user.id):
                return await message.reply("❌ Unauthorized!")
            
            if len(message.command) < 2:
                current = self.config.get('loudness', 0)
                return await message.reply(f"📊 **Current Loudness:** `{current}%`\n\nRange: 0-100%\nUsage: `/loudness 75`")
            
            try:
                loudness = float(message.command[1])
                if AudioEffects.validate_value(loudness, 0, 100):
                    self.config['loudness'] = loudness
                    await self._save_config()
                    
                    if message.chat.id in self.audio_bridge.active_bridges:
                        await self.audio_bridge.update_effects(message.chat.id, loudness=loudness)
                    
                    bar = self._create_visual_bar(loudness, 100, 20)
                    await message.reply(f"✅ **Loudness: `{loudness}%`**\n\n{bar}")
                else:
                    await message.reply("❌ Loudness must be between 0 and 100!")
            except ValueError:
                await message.reply("❌ Invalid value!")
        
        @self.bot.on_message(filters.command("bass") & filters.group)
        async def bass_cmd(client, message: Message):
            if not self._is_sudo(message.from_user.id):
                return await message.reply("❌ Unauthorized!")
            
            if len(message.command) < 2:
                current = self.config.get('bass', 0)
                return await message.reply(
                    f"**🎵 Bass Boost Settings**\n\n"
                    f"Current: `{current}%`\n"
                    f"Range: 0-100%\n\n"
                    f"Usage: `/bass 50`\n\n"
                    f"**Effect Levels:**\n"
                    f"• 0% = No boost\n"
                    f"• 30% = Mild bass\n"
                    f"• 60% = Strong bass\n"
                    f"• 100% = Maximum bass"
                )
            
            try:
                bass = float(message.command[1])
                if AudioEffects.validate_value(bass, 0, 100):
                    self.config['bass'] = bass
                    await self._save_config()
                    
                    if message.chat.id in self.audio_bridge.active_bridges:
                        await self.audio_bridge.update_effects(message.chat.id, bass=bass)
                    
                    # Visual bass bars
                    bars = "🔊" + "🔉" * int(bass / 10) + "🔈" * (10 - int(bass / 10))
                    await message.reply(f"✅ **Bass Boost: `{bass}%`**\n\n{bars}")
                else:
                    await message.reply("❌ Bass must be between 0 and 100!")
            except ValueError:
                await message.reply("❌ Invalid value!")
        
        @self.bot.on_message(filters.command("effects"))
        async def effects_cmd(client, message: Message):
            effects = self.config
            
            # Create visual representation
            gain_bar = self._create_visual_bar(effects.get('gain', 100), 500, 10)
            echo_bar = self._create_visual_bar(effects.get('echo', 0), 100, 10)
            loudness_bar = self._create_visual_bar(effects.get('loudness', 0), 100, 10)
            bass_bar = self._create_visual_bar(effects.get('bass', 0), 100, 10)
            
            text = f"""
**🎛️ Audio Effects Dashboard**

┌─────────────────────────────────┐
│ **GAIN**     | {gain_bar} | `{effects.get('gain', 100)}%` │
│ **ECHO**     | {echo_bar} | `{effects.get('echo', 0)}%` │
│ **LOUDNESS** | {loudness_bar} | `{effects.get('loudness', 0)}%` │
│ **BASS**     | {bass_bar} | `{effects.get('bass', 0)}%` │
└─────────────────────────────────┘

**Commands:**
`/gain 150` - Increase volume
`/echo 50` - Add echo effect
`/loudness 75` - Normalize audio
`/bass 60` - Boost bass
`/reset` - Reset all effects

**Presets:** `/preset club`, `/preset voice`, `/preset concert`
"""
            await message.reply(text)
        
        @self.bot.on_message(filters.command("preset"))
        async def preset_cmd(client, message: Message):
            if not self._is_sudo(message.from_user.id):
                return await message.reply("❌ Unauthorized!")
            
            if len(message.command) < 2:
                return await message.reply(
                    "**🎛️ Available Presets**\n\n"
                    "`/preset club` - Heavy bass (G:150, E:20, L:30, B:70)\n"
                    "`/preset concert` - Live sound (G:130, E:50, L:40, B:40)\n"
                    "`/preset voice` - Clear voice (G:120, E:10, L:60, B:20)\n"
                    "`/preset radio` - FM style (G:100, E:15, L:30, B:30)\n"
                    "`/preset default` - Reset to default"
                )
            
            preset_name = message.command[1].lower()
            preset = AudioEffects.get_preset(preset_name)
            
            if preset:
                self.config.update(preset)
                await self._save_config()
                
                if message.chat.id in self.audio_bridge.active_bridges:
                    await self.audio_bridge.update_effects(message.chat.id, **preset)
                
                await message.reply(
                    f"✅ **Preset '{preset_name}' applied!**\n\n"
                    f"Gain: `{preset['gain']}%` | Echo: `{preset['echo']}%`\n"
                    f"Loudness: `{preset['loudness']}%` | Bass: `{preset['bass']}%`"
                )
            else:
                await message.reply(f"❌ Preset '{preset_name}' not found!")
        
        @self.bot.on_message(filters.command("reset"))
        async def reset_cmd(client, message: Message):
            if not self._is_sudo(message.from_user.id):
                return await message.reply("❌ Unauthorized!")
            
            self.config = AudioEffects.get_default_effects()
            await self._save_config()
            
            if message.chat.id in self.audio_bridge.active_bridges:
                await self.audio_bridge.update_effects(message.chat.id, **self.config)
            
            await message.reply("✅ **All effects reset to default!**\n\nGain: 100%, Echo: 0%, Loudness: 0%, Bass: 0%")
    
    def _create_visual_bar(self, value: float, max_val: float, length: int = 10) -> str:
        """Create visual bar for effect display"""
        filled = int((value / max_val) * length)
        empty = length - filled
        return "█" * filled + "░" * empty
    
    async def _save_config(self):
        with open('bridge_config.json', 'w') as f:
            json.dump({'effects': self.config}, f, indent=4)
    
    def _is_sudo(self, user_id: int) -> bool:
        from config.settings import SUDO_USERS
        return user_id in SUDO_USERS