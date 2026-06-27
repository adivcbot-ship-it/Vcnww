import os
import subprocess
import asyncio
import logging
import time
from typing import Dict, Optional
from pathlib import Path
from pytgcalls import PyTgCalls
from pytgcalls.types import AudioPiped, AudioQuality
from config.settings import DEFAULT_RADIO_URL, TEMP_DIR

logger = logging.getLogger(__name__)

class AudioBridge:
    def __init__(self, client: PyTgCalls):
        self.client = client
        self.active_bridges: Dict[int, dict] = {}
        self.ffmpeg_processes: Dict[int, subprocess.Popen] = {}
        self.config = {'gain': 100, 'echo': 0, 'loudness': 0, 'bass': 0}
        self.radio_process: Optional[subprocess.Popen] = None
        self.main_fifo: Optional[str] = None
        
        # Create temp directory
        Path(TEMP_DIR).mkdir(exist_ok=True)
        
    def _create_audio_source(self, audio_source: str = None) -> str:
        """Create continuous audio source"""
        self.main_fifo = f"{TEMP_DIR}/main_audio_stream.raw"
        
        if os.path.exists(self.main_fifo):
            try:
                os.remove(self.main_fifo)
            except:
                pass
        
        os.mkfifo(self.main_fifo)
        
        if not audio_source:
            audio_source = DEFAULT_RADIO_URL
        
        ffmpeg_cmd = [
            'ffmpeg', '-re', '-i', audio_source,
            '-f', 's16le', '-ar', '48000', '-ac', '2',
            '-y', self.main_fifo
        ]
        
        self.radio_process = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL
        )
        
        time.sleep(3)
        return self.main_fifo
    
    def _build_filter_chain(self, gain: float = 100, echo: float = 0, 
                            loudness: float = 0, bass: float = 0) -> str:
        """Build FFmpeg audio filter chain"""
        filters = []
        
        # Gain/Volume (0-500%)
        if gain != 100:
            volume = max(0.0, min(5.0, gain / 100))
            filters.append(f"volume={volume}")
        
        # Echo effect (0-100%)
        if echo > 0:
            delay = 60
            decay = max(0.1, min(0.9, echo / 100))
            filters.append(f"aecho=0.8:0.9:{delay}:{decay}")
        
        # Loudness normalization (0-100%)
        if loudness > 0:
            lra = max(1, min(50, loudness * 2))
            filters.append(f"loudnorm=I=-16:LRA={lra}:TP=-1.5")
        
        # Bass boost (0-100%)
        if bass > 0:
            gain_db = bass / 5
            filters.append(f"bass=g={gain_db}:f=100:w=0.5")
        
        # Quality improvements
        filters.append("acompressor=threshold=0.1:ratio=2:attack=5:release=50")
        filters.append("highpass=f=80,lowpass=f=15000")
        filters.append("dynaudnorm=p=0.9")
        
        return ",".join(filters) if filters else "anull"
    
    async def start_bridge(self, source_id: int, target_id: int, 
                          gain: float = 100, echo: float = 0, 
                          loudness: float = 0, bass: float = 0,
                          audio_source: str = None) -> bool:
        """Start bridge between source and target"""
        try:
            # Create main audio source if not exists
            if not self.radio_process or self.radio_process.poll() is not None:
                self._create_audio_source(audio_source)
            
            bridge_id = f"{source_id}_{target_id}"
            fifo_path = f"{TEMP_DIR}/bridge_{bridge_id}.raw"
            
            if os.path.exists(fifo_path):
                os.remove(fifo_path)
            os.mkfifo(fifo_path)
            
            # Build filter chain
            filter_chain = self._build_filter_chain(gain, echo, loudness, bass)
            
            ffmpeg_cmd = [
                'ffmpeg', '-f', 's16le', '-ar', '48000', '-ac', '2', '-re',
                '-i', self.main_fifo,
                '-af', filter_chain,
                '-f', 's16le', '-ar', '48000', '-ac', '2',
                '-y', fifo_path
            ]
            
            process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL
            )
            self.ffmpeg_processes[source_id] = process
            
            await asyncio.sleep(2)
            
            # Join voice chats
            await self.client.join_group_call(source_id, AudioPiped(fifo_path, AudioQuality.HIGH))
            await self.client.join_group_call(target_id, AudioPiped(fifo_path, AudioQuality.HIGH))
            
            self.active_bridges[source_id] = {
                'target_id': target_id,
                'fifo_path': fifo_path,
                'gain': gain,
                'echo': echo,
                'loudness': loudness,
                'bass': bass,
                'audio_source': audio_source,
                'started_at': time.time()
            }
            
            logger.info(f"✅ Bridge started: {source_id} -> {target_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start bridge: {e}")
            return False
    
    async def update_effects(self, source_id: int, gain: float = None, 
                            echo: float = None, loudness: float = None,
                            bass: float = None) -> bool:
        """Update effects for active bridge"""
        if source_id not in self.active_bridges:
            return False
        
        bridge = self.active_bridges[source_id]
        if gain is not None:
            bridge['gain'] = gain
        if echo is not None:
            bridge['echo'] = echo
        if loudness is not None:
            bridge['loudness'] = loudness
        if bass is not None:
            bridge['bass'] = bass
        
        # Restart bridge with new effects
        target_id = bridge['target_id']
        audio_source = bridge.get('audio_source')
        
        await self.stop_bridge(source_id)
        return await self.start_bridge(
            source_id, target_id,
            bridge['gain'], bridge['echo'], 
            bridge['loudness'], bridge['bass'],
            audio_source
        )
    
    async def stop_bridge(self, source_id: int) -> bool:
        """Stop active bridge"""
        if source_id not in self.active_bridges:
            return False
        
        bridge = self.active_bridges[source_id]
        try:
            await self.client.leave_group_call(source_id)
            await self.client.leave_group_call(bridge['target_id'])
            
            if source_id in self.ffmpeg_processes:
                self.ffmpeg_processes[source_id].terminate()
                del self.ffmpeg_processes[source_id]
            
            if os.path.exists(bridge['fifo_path']):
                os.remove(bridge['fifo_path'])
            
            del self.active_bridges[source_id]
            logger.info(f"✅ Bridge stopped: {source_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to stop bridge: {e}")
            return False
    
    async def stop_all_bridges(self) -> int:
        """Stop all bridges"""
        count = 0
        for source_id in list(self.active_bridges.keys()):
            if await self.stop_bridge(source_id):
                count += 1
        
        # Cleanup main audio source
        if self.radio_process:
            self.radio_process.terminate()
            self.radio_process = None
        
        if self.main_fifo and os.path.exists(self.main_fifo):
            try:
                os.remove(self.main_fifo)
            except:
                pass
        
        return count
    
    def get_bridge_count(self) -> int:
        return len(self.active_bridges)