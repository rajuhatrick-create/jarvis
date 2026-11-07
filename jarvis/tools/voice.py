"""
Voice Control - Speech recognition and text-to-speech using Edge TTS
"""

import logging
import asyncio
import threading
from typing import Optional

logger = logging.getLogger('JARVIS.tools.voice')


class VoiceControl:
    """Handle speech recognition and text-to-speech using Edge TTS"""
    
    def __init__(self, config: dict):
        self.config = config.get('voice', {})
        self.language = self.config.get('language', 'en-IN')
        self.tts_voice_index = self.config.get('tts_voice', 0)
        self.wake_word = self.config.get('wake_word', 'jarvis')
        self.speak_enabled = self.config.get('speak_enabled', True)
        self.speak_rate = self.config.get('speak_rate', 0)  # Edge TTS: rate in percent (-100 to +100)
        self.speak_volume = self.config.get('speak_volume', 0)  # Edge TTS: volume change percent
        
        self.speech_recognizer = None
        self.tts_available = False
        self.edge_voice = "en-IN-PrabhatNeural"  # Default Indian English male voice (JARVIS-like)
        self._event_loop = None
        self._loop_thread = None
        
        self._init_speech_recognition()
        self._init_tts()
        logger.info("VoiceControl initialized")
    
    def _init_speech_recognition(self):
        """Initialize speech recognition"""
        try:
            import speech_recognition as sr
            self.speech_recognizer = sr.Recognizer()
            self.speech_recognizer.pause_threshold = 1
            self.speech_recognizer.energy_threshold = 300
            logger.info("Speech recognition initialized")
        except ImportError:
            logger.warning("SpeechRecognition not installed. Voice input disabled.")
            self.speech_recognizer = None
    
    def _init_tts(self):
        """Initialize Edge TTS"""
        try:
            import edge_tts
            # Set up a dedicated event loop for edge-tts async calls
            def run_loop():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                self._event_loop = loop
                loop.run_forever()
            
            self._loop_thread = threading.Thread(target=run_loop, daemon=True)
            self._loop_thread.start()
            # Wait for loop to be ready
            import time
            for _ in range(50):
                if self._event_loop:
                    break
                time.sleep(0.01)
            
            self.tts_available = True
            logger.info(f"Edge TTS initialized with voice: {self.edge_voice}")
        except ImportError:
            logger.warning("edge-tts not installed. Text-to-speech disabled.")
            self.tts_available = False
    
    async def _speak_edge(self, text: str):
        """Speak text using Edge TTS (async)"""
        try:
            import edge_tts
            
            # Check if pygame is available (Windows only)
            try:
                import pygame
                has_pygame = True
            except ImportError:
                has_pygame = False
                logger.warning("pygame not available — TTS audio will not play (cloud mode)")
            
            # Edge TTS rate format: "+0%", "+10%", "-10%" etc.
            rate_str = f"+{self.speak_rate}%" if self.speak_rate >= 0 else f"{self.speak_rate}%"
            communicate = edge_tts.Communicate(
                text, 
                self.edge_voice,
                rate=rate_str
            )
            
            # Create a temporary file for the audio
            import tempfile
            import os
            temp_file = tempfile.mktemp(suffix='.mp3')
            
            await communicate.save(temp_file)
            
            # Play the audio only if pygame is available (local mode)
            if has_pygame:
                if not hasattr(self, '_pygame_initialized'):
                    pygame.mixer.init()
                    self._pygame_initialized = True
                pygame.mixer.music.load(temp_file)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    await asyncio.sleep(0.1)
            
            # Clean up
            try:
                os.unlink(temp_file)
            except OSError:
                pass  # File already cleaned up
            
        except Exception as e:
            logger.error(f"Edge TTS error: {e}")
    
    def speak_async(self, text: str):
        """Speak text in background so it doesn't block the server"""
        if not self.speak_enabled or not self.tts_available:
            return
        
        if self._event_loop:
            try:
                asyncio.run_coroutine_threadsafe(
                    self._speak_edge(text), 
                    self._event_loop
                )
            except Exception as e:
                logger.error(f"Failed to schedule TTS: {e}")
    
    def toggle_speak(self, enabled: bool):
        """Toggle speaking on/off"""
        self.speak_enabled = enabled
        logger.info(f"Speaking {'enabled' if enabled else 'disabled'}")
    
    def speak(self, text: str):
        """Convert text to speech (blocking)"""
        if not self.tts_available:
            logger.info(f"[TTS not available] {text}")
            return
        
        if self._event_loop:
            try:
                asyncio.run_coroutine_threadsafe(
                    self._speak_edge(text), 
                    self._event_loop
                ).result(timeout=10)
            except Exception as e:
                logger.error(f"TTS error: {e}")
    
    def listen(self, timeout: int = 5, phrase_timeouint: int = 5) -> Optional[str]:
        """Listen for speech and return recognized text"""
        if not self.speech_recognizer:
            return None
        
        try:
            import speech_recognition as sr
            with sr.Microphone() as source:
                logger.info("Listening...")
                self.speech_recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = self.speech_recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_timeouint=phrase_timeouint
                )
            
            logger.info("Recognizing...")
            # Try Google Web Speech API (free, requires internet)
            try:
                text = self.speech_recognizer.recognize_google(audio, language=self.language)
                logger.info(f"Recognized: {text}")
                return text
            except sr.UnknownValueError:
                logger.info("Could not understand audio")
                return None
            except sr.RequestError as e:
                logger.error(f"Speech recognition service error: {e}")
                # Fallback to offline recognition if available
                try:
                    text = self.speech_recognizer.recognize_sphinx(audio, language=self.language)
                    return text
                except Exception:
                    return None
        except Exception as e:
            logger.error(f"Voice input error: {e}")
            return None
    
    def get_available_voices(self) -> list:
        """Get list of available Edge TTS voices"""
        if not self.tts_available:
            return []
        # Common Edge TTS voices
        voices = [
            {'index': 0, 'name': 'Prabhat (Male, en-IN)', 'id': 'en-IN-PrabhatNeural'},
            {'index': 1, 'name': 'Neerja (Female, en-IN)', 'id': 'en-IN-NeerjaNeural'},
            {'index': 2, 'name': 'Jenny (Female, en-US)', 'id': 'en-US-JennyNeural'},
            {'index': 3, 'name': 'Guy (Male, en-US)', 'id': 'en-US-GuyNeural'},
            {'index': 4, 'name': 'Sonia (Female, en-GB)', 'id': 'en-GB-SoniaNeural'},
            {'index': 5, 'name': 'Ryan (Male, en-GB)', 'id': 'en-GB-RyanNeural'},
        ]
        return voices
    
    def is_available(self) -> dict:
        """Check if voice features are available"""
        return {
            'speech_recognition': self.speech_recognizer is not None,
            'text_to_speech': self.tts_available,
            'speak_enabled': self.speak_enabled,
            'voices': self.get_available_voices() if self.tts_available else []
        }
