import asyncio
import logging
from typing import Dict, Optional, List
from pyrogram import Client
from pyrogram.errors import UserNotParticipant, FloodWait, SessionRevoked
from pyrogram.raw.functions.phone import CreateGroupCall
from pytgcalls import PyTgCalls
import time

logger = logging.getLogger(__name__)

class AssistantManager:
    def __init__(self, api_id: int, api_hash: str):
        self.api_id = api_id
        self.api_hash = api_hash
        self.assistants: Dict[str, dict] = {}
        
    async def add_assistant(self, session_string: str, name: str = None) -> bool:
        """Add a new assistant using session string"""
        try:
            client = Client(
                name or f"assistant_{int(time.time())}",
                api_id=self.api_id,
                api_hash=self.api_hash,
                session_string=session_string,
                in_memory=False
            )
            await client.start()
            me = await client.get_me()
            
            bridge = PyTgCalls(client)
            await bridge.start()
            
            self.assistants[session_string] = {
                'client': client,
                'bridge': bridge,
                'user_id': me.id,
                'name': me.first_name,
                'username': me.username,
                'added_at': time.time()
            }
            logger.info(f"✅ Assistant added: {me.first_name} (@{me.username})")
            return True
        except SessionRevoked:
            logger.error("Session string invalid or revoked")
            return False
        except Exception as e:
            logger.error(f"Failed to add assistant: {e}")
            return False
    
    async def remove_assistant(self, session_string: str) -> bool:
        """Remove an assistant"""
        if session_string in self.assistants:
            try:
                await self.assistants[session_string]['client'].stop()
            except:
                pass
            del self.assistants[session_string]
            logger.info("Assistant removed")
            return True
        return False
    
    def get_assistant(self, index: int = 0) -> Optional[dict]:
        """Get assistant by index"""
        if self.assistants:
            return list(self.assistants.values())[index]
        return None
    
    def get_all_assistants(self) -> List[dict]:
        """Get all assistants"""
        return list(self.assistants.values())
    
    def get_assistant_count(self) -> int:
        """Get number of assistants"""
        return len(self.assistants)
    
    async def check_membership(self, assistant_session: str, chat_id: int) -> bool:
        """Check if assistant is member of chat"""
        assistant = self.assistants.get(assistant_session)
        if not assistant:
            return False
        try:
            member = await assistant['client'].get_chat_member(chat_id, "me")
            return member is not None
        except UserNotParticipant:
            return False
        except Exception as e:
            logger.error(f"Membership check error: {e}")
            return False
    
    async def start_voice_chat(self, assistant_session: str, chat_id: int) -> bool:
        """Start voice chat in a group"""
        assistant = self.assistants.get(assistant_session)
        if not assistant:
            return False
        try:
            peer = await assistant['client'].resolve_peer(chat_id)
            await assistant['client'].invoke(
                CreateGroupCall(
                    peer=peer,
                    random_id=int(time.time() * 1000) % 1000000
                )
            )
            await asyncio.sleep(2)
            return True
        except Exception as e:
            logger.warning(f"Could not start voice chat: {e}")
            return False
    
    async def leave_voice_chat(self, assistant_session: str, chat_id: int) -> bool:
        """Leave voice chat"""
        assistant = self.assistants.get(assistant_session)
        if not assistant:
            return False
        try:
            await assistant['bridge'].leave_group_call(chat_id)
            return True
        except Exception as e:
            logger.warning(f"Could not leave voice chat: {e}")
            return False
