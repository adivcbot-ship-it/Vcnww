import os
import subprocess
import asyncio
import logging
import time
from typing import Dict, Optional
from pathlib import Path
from config.settings import TEMP_DIR, SCREENSHARE_QUALITY, SCREENSHARE_FPS

logger = logging.getLogger(__name__)

class ScreenshareManager:
    def __init__(self):
        self.active_screenshares: Dict[int, dict] = {}
        self.ffmpeg_processes: Dict[int, subprocess.Popen] = {}
        
    async def start_screenshare(self, chat_id: int, pytgcalls_client, 
                                quality: str = SCREENSHARE_QUALITY, 
                                fps: int = SCREENSHARE_FPS,
                                include_audio: bool = True) -> bool:
        """Start screenshare in voice chat"""
        try:
            if chat_id in self.active_screenshares:
                return False
            
            # Create FIFO for screenshare
            fifo_path = f"{TEMP_DIR}/screenshare_{chat_id}.raw"
            if os.path.exists(fifo_path):
                os.remove(fifo_path)
            os.mkfifo(fifo_path)
            
            # Get screen capture command
            screen_cmd = self._get_screen_capture_command(fifo_path, quality, fps, include_audio)
            
            # Start FFmpeg process
            process = subprocess.Popen(
                screen_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                shell=True,
                executable='/bin/bash'
            )
            self.ffmpeg_processes[chat_id] = process
            
            await asyncio.sleep(3)
            
            # Join voice chat with screenshare stream
            try:
                from pytgcalls.types import AudioPiped, VideoPiped
                from pytgcalls.types.input_stream import AudioVideoPiped
                
                await pytgcalls_client.join_group_call(
                    chat_id,
                    AudioVideoPiped(
                        AudioPiped(fifo_path),
                        VideoPiped(fifo_path)
                    )
                )
            except:
                # Fallback to audio only
                await pytgcalls_client.join_group_call(
                    chat_id,
                    AudioPiped(fifo_path)
                )
            
            # Also take a screenshot for preview
            preview_path = await self._take_screenshot(chat_id)
            
            self.active_screenshares[chat_id] = {
                'fifo_path': fifo_path,
                'quality': quality,
                'fps': fps,
                'started_at': time.time(),
                'preview': preview_path
            }
            
            logger.info(f"✅ Screenshare started in chat {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start screenshare: {e}")
            return False
    
    def _get_screen_capture_command(self, output_fifo: str, quality: str, fps: int, include_audio: bool) -> str:
        """Get FFmpeg command for screen capture"""
        
        # Quality settings
        quality_map = {
            "480p": "854x480",
            "720p": "1280x720",
            "1080p": "1920x1080"
        }
        resolution = quality_map.get(quality, "1280x720")
        
        import sys
        if sys.platform.startswith('linux'):
            # Linux with X11
            cmd = f'ffmpeg -f x11grab -video_size {resolution} -framerate {fps} -i :0.0+0,0 '
            if include_audio:
                cmd += f'-f pulse -i default '
            cmd += f'-f s16le -ar 48000 -ac 2 -y {output_fifo} 2>/dev/null'
            
        elif sys.platform.startswith('win'):
            # Windows
            cmd = f'ffmpeg -f gdigrab -framerate {fps} -i desktop '
            if include_audio:
                cmd += f'-f dshow -i audio="Microphone" '
            cmd += f'-f s16le -ar 48000 -ac 2 -y {output_fifo} 2>/dev/null'
            
        elif sys.platform.startswith('darwin'):
            # macOS
            cmd = f'ffmpeg -f avfoundation -framerate {fps} -i "1" '
            if include_audio:
                cmd += f'-i ":0" '
            cmd += f'-f s16le -ar 48000 -ac 2 -y {output_fifo} 2>/dev/null'
        else:
            # Fallback - test pattern
            cmd = f'ffmpeg -f lavfi -i testsrc=size={resolution}:rate={fps} '
            cmd += f'-f s16le -ar 48000 -ac 2 -y {output_fifo} 2>/dev/null'
        
        return cmd
    
    async def _take_screenshot(self, chat_id: int) -> Optional[str]:
        """Take screenshot for preview"""
        try:
            screenshot_path = f"{TEMP_DIR}/screenshot_{chat_id}.png"
            
            # Try different screenshot tools
            if subprocess.call(['which', 'scrot'], stdout=subprocess.DEVNULL) == 0:
                subprocess.call(['scrot', screenshot_path])
            elif subprocess.call(['which', 'import'], stdout=subprocess.DEVNULL) == 0:
                subprocess.call(['import', '-window', 'root', screenshot_path])
            else:
                # Create dummy message
                return None
            
            return screenshot_path if os.path.exists(screenshot_path) else None
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            return None
    
    async def stop_screenshare(self, chat_id: int) -> bool:
        """Stop screenshare"""
        if chat_id not in self.active_screenshares:
            return False
        
        try:
            # Kill FFmpeg process
            if chat_id in self.ffmpeg_processes:
                self.ffmpeg_processes[chat_id].terminate()
                try:
                    self.ffmpeg_processes[chat_id].wait(timeout=5)
                except:
                    self.ffmpeg_processes[chat_id].kill()
                del self.ffmpeg_processes[chat_id]
            
            # Remove FIFO
            fifo_path = self.active_screenshares[chat_id]['fifo_path']
            if os.path.exists(fifo_path):
                os.remove(fifo_path)
            
            # Clean up preview
            preview = self.active_screenshares[chat_id].get('preview')
            if preview and os.path.exists(preview):
                os.remove(preview)
            
            del self.active_screenshares[chat_id]
            logger.info(f"✅ Screenshare stopped in chat {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stop screenshare: {e}")
            return False
    
    def is_active(self, chat_id: int) -> bool:
        return chat_id in self.active_screenshares
    
    def get_preview(self, chat_id: int) -> Optional[str]:
        """Get screenshot preview path"""
        if chat_id in self.active_screenshares:
            return self.active_screenshares[chat_id].get('preview')
        return None
    
    async def stop_all(self) -> int:
        """Stop all screenshares"""
        count = 0
        for chat_id in list(self.active_screenshares.keys()):
            if await self.stop_screenshare(chat_id):
                count += 1
        return count
