import logging
from typing import Dict

logger = logging.getLogger(__name__)

class AudioEffects:
    """Audio effects processor for audio streams"""
    
    @staticmethod
    def build_ffmpeg_filter(gain: float = 100, echo: float = 0, 
                            loudness: float = 0, bass: float = 0, 
                            treble: float = 0) -> str:
        """
        Build FFmpeg audio filter chain
        
        Args:
            gain: Volume level (0-500%)
            echo: Echo effect (0-100%)
            loudness: Loudness normalization (0-100%)
            bass: Bass boost (0-100%)
            treble: Treble boost (0-100%)
        
        Returns:
            FFmpeg filter string
        """
        filters = []
        
        # Volume/Gain (0-500%)
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
            gain_db = bass / 5  # 0-20dB
            filters.append(f"bass=g={gain_db}:f=100:w=0.5")
            filters.append(f"aequalizer=100:0.5:{gain_db}")
        
        # Treble boost (0-100%)
        if treble > 0:
            gain_db = treble / 5
            filters.append(f"treble=g={gain_db}:f=10000:w=0.5")
            filters.append(f"aequalizer=10000:0.5:{gain_db}")
        
        # Dynamic compression
        filters.append("acompressor=threshold=0.1:ratio=2:attack=5:release=50")
        
        # Frequency filtering
        filters.append("highpass=f=80,lowpass=f=15000")
        
        # Dynamic normalization
        filters.append("dynaudnorm=p=0.9")
        
        filter_str = ",".join(filters) if filters else "anull"
        logger.debug(f"Built filter chain: {filter_str}")
        return filter_str
    
    @staticmethod
    def get_default_effects() -> Dict:
        """Get default effects configuration"""
        return {
            'gain': 100,
            'echo': 0,
            'loudness': 0,
            'bass': 0,
            'treble': 0
        }
    
    @staticmethod
    def validate_value(value: float, min_val: float, max_val: float) -> bool:
        """Validate if value is within range"""
        return min_val <= value <= max_val
    
    @staticmethod
    def get_preset(preset_name: str) -> Dict:
        """Get preset effects configuration"""
        presets = {
            'club': {'gain': 150, 'echo': 20, 'loudness': 30, 'bass': 70},
            'concert': {'gain': 130, 'echo': 50, 'loudness': 40, 'bass': 40},
            'voice': {'gain': 120, 'echo': 10, 'loudness': 60, 'bass': 20},
            'radio': {'gain': 100, 'echo': 15, 'loudness': 30, 'bass': 30},
            'default': {'gain': 100, 'echo': 0, 'loudness': 0, 'bass': 0}
        }
        return presets.get(preset_name, presets['default'])
    
    @staticmethod
    def calculate_delay_ms(echo: float) -> int:
        """Calculate delay in milliseconds based on echo percentage"""
        return int(60 + (echo * 0.4))
    
    @staticmethod
    def calculate_decay(echo: float) -> float:
        """Calculate decay factor based on echo percentage"""
        return max(0.1, min(0.9, echo / 100))