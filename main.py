#!/usr/bin/env python3
"""
VCFight V2 - Advanced Voice Chat Bot with Screenshare
Complete working version for Telegram
"""

import asyncio
import logging
import sys
import json
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from pyrogram import Client, idle
from config.settings import API_ID, API_HASH, BOT_TOKEN
from core.assistant import AssistantManager
from core.bridge import AudioBridge
from core.database import DatabaseManager
from core.screenshare import ScreenshareManager
from plugins.bridge_commands import BridgeCommands
from plugins.audio_effects import AudioEffectsCommands
from plugins.admin_commands import AdminCommands
from plugins.stream_commands import StreamCommands
from plugins.vc_commands import VCCommands

# Setup logging
logger = logging.getLogger(__name__)

class VCFightBot:
    def __init__(self):
        self.bot = Client("VCFightV2", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
        self.assistant_manager = AssistantManager(API_ID, API_HASH)
        self.db = DatabaseManager()
        self.screenshare_manager = ScreenshareManager()
        self.audio_bridge = None
        self.config = self._load_config()
        
    def _load_config(self):
        """Load configuration from file"""
        config_file = Path("bridge_config.json")
        if config_file.exists():
            with open(config_file, 'r') as f:
                data = json.load(f)
                return data.get('effects', {'gain': 100, 'echo': 0, 'loudness': 0, 'bass': 0})
        return {'gain': 100, 'echo': 0, 'loudness': 0, 'bass': 0}
    
    def _save_config(self):
        """Save configuration to file"""
        with open("bridge_config.json", 'w') as f:
            json.dump({'effects': self.config}, f, indent=4)
        
    async def start(self):
        """Start the bot"""
        print("\n" + "="*60)
        print("🎙️ VCFight V2 - Advanced Voice Chat Bot")
        print("="*60)
        print("Version: 2.0.0")
        print("Features:")
        print("  • Voice Chat Bridge")
        print("  • Screenshare Support")
        print("  • Bass/Echo/Loudness Effects")
        print("  • Leave/Join VC Commands")
        print("  • YouTube/Radio Streaming")
        print("="*60 + "\n")
        
        # Start bot
        await self.bot.start()
        print("✅ Bot started successfully!")
        
        # Restore assistants from database
        assistants = self.db.get_assistants()
        if assistants:
            print(f"\n📀 Restoring {len(assistants)} assistant(s)...")
            for ass in assistants:
                try:
                    result = await self.assistant_manager.add_assistant(ass.session_string, ass.name)
                    if result:
                        print(f"  ✅ Restored: {ass.name}")
                    else:
                        print(f"  ❌ Failed to restore: {ass.name}")
                except Exception as e:
                    print(f"  ❌ Error restoring {ass.name}: {e}")
        else:
            print("\n⚠️ No assistants found! Use /addstring in private chat to add one.")
        
        # Initialize audio bridge
        assistant_data = self.assistant_manager.get_assistant()
        if assistant_data:
            self.audio_bridge = AudioBridge(assistant_data['bridge'])
            self.audio_bridge.config = self.config
            print("✅ Audio bridge initialized!")
        else:
            self.audio_bridge = None
            print("⚠️ Audio bridge not initialized (no assistant)")
        
        # Initialize all plugins
        BridgeCommands(self.bot, self.assistant_manager, self.audio_bridge, self.db)
        AudioEffectsCommands(self.bot, self.audio_bridge, self.config, self.assistant_manager)
        AdminCommands(self.bot, self.assistant_manager, self.db, self.audio_bridge)
        StreamCommands(self.bot, self.assistant_manager, self.audio_bridge)
        VCCommands(self.bot, self.assistant_manager, self.audio_bridge, self.screenshare_manager)
        
        print("\n" + "🎙️"*30)
        print("🎙️ VCFight V2 IS ONLINE AND READY!")
        print("\n📝 Available Commands:")
        print("   🔹 Voice Chat:")
        print("      /bridge <target> - Start audio bridge")
        print("      /leavevc - Leave voice chat")
        print("      /joinvc - Join voice chat")
        print("      /vcstatus - Check voice chat status")
        print("\n   🔹 Screenshare:")
        print("      /screenshare [quality] [fps] - Start screenshare")
        print("      /screenshareoff - Stop screenshare")
        print("\n   🔹 Audio Effects:")
        print("      /bass <0-100> - Set bass boost")
        print("      /echo <0-100> - Set echo effect")
        print("      /loudness <0-100> - Set loudness")
        print("      /gain <0-500> - Set volume level")
        print("      /effects - Show all effects")
        print("      /preset <name> - Apply preset")
        print("      /reset - Reset all effects")
        print("\n   🔹 Streaming:")
        print("      /radio <url> - Play radio stream")
        print("      /yt <url> - Play YouTube audio")
        print("      /play - Reply to audio file")
        print("\n   🔹 Admin:")
        print("      /addstring - Add assistant (PM only)")
        print("      /removeassistant - Remove assistant (PM)")
        print("      /assistants - List assistants (PM)")
        print("      /stopall - Stop all bridges")
        print("      /bridges - List active bridges")
        print("🎙️"*30 + "\n")
        
        # Keep bot running
        await idle()
        
        # Cleanup on shutdown
        print("\n🛑 Shutting down...")
        if self.audio_bridge:
            await self.audio_bridge.stop_all_bridges()
        await self.screenshare_manager.stop_all()
        await self.bot.stop()
        print("👋 Goodbye!")

async def main():
    """Main entry point"""
    try:
        bot = VCFightBot()
        await bot.start()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
