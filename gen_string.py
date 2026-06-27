#!/usr/bin/env python3
"""
Generate Pyrogram session string for assistant bot
"""

import asyncio
from pyrogram import Client

async def main():
    print("\n" + "="*50)
    print("🔐 VCFight V2 - Session String Generator")
    print("="*50)
    
    api_id = int(input("\n📱 Enter your API ID: "))
    api_hash = input("🔑 Enter your API HASH: ")
    
    print("\n📋 You will now be asked to login with your phone number.")
    print("⚠️ Make sure you have a Telegram account for the assistant bot.\n")
    
    app = Client("session_gen", api_id=api_id, api_hash=api_hash)
    
    try:
        await app.start()
        me = await app.get_me()
        session_string = await app.export_session_string()
        
        print("\n" + "="*50)
        print("✅ SESSION STRING GENERATED SUCCESSFULLY!")
        print("="*50)
        print(f"\n📋 COPY THIS STRING (Keep it safe!):\n")
        print(session_string)
        print("\n" + "="*50)
        print(f"👤 Account: {me.first_name} (@{me.username})")
        print(f"🆔 User ID: {me.id}")
        print("="*50)
        print("\n⚠️ Never share this session string with anyone!")
        print("Use /addstring in bot PM to add this assistant.\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        await app.stop()

if __name__ == "__main__":
    asyncio.run(main())