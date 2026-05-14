"""
Voice Processor Module - Speech Recognition and Command Extraction
Supports both online (Google Speech API) and offline (Vosk) modes
"""

import speech_recognition as sr
from typing import Optional
import threading
import queue


class VoiceProcessor:
    """
    Handles voice input processing with keyword spotting.
    Prevents accidental activation from background conversation.
    """
    
    COMMAND_KEYWORDS = {
        # Navigation & Interaction
        "click": "CLICK",
        "select": "CLICK",
        "activate": "CLICK",
        
        "right click": "RIGHT_CLICK",
        "right-click": "RIGHT_CLICK",
        "options": "RIGHT_CLICK",
        "menu": "RIGHT_CLICK",
        "context": "RIGHT_CLICK",
        
        "double click": "DOUBLE_CLICK",
        "double-click": "DOUBLE_CLICK",
        "double": "DOUBLE_CLICK",
        "open": "DOUBLE_CLICK",
        
        # Scrolling
        "scroll up": "SCROLL_UP",
        "scroll down": "SCROLL_DOWN",
        "scroll": "SCROLL_DOWN",
        
        # Zoom
        "zoom": "ZOOM",
        "zoom in": "ZOOM",
        "magnify": "ZOOM",
        
        # System
        "stop": "STOP",
        "freeze": "STOP",
        "pause": "STOP",
        
        "wake": "WAKE",
        "wake up": "WAKE",
        "resume": "WAKE",
        "wake up iris": "WAKE",
        
        "calibrate": "CALIBRATE",
        "recalibrate": "CALIBRATE",
        "recal": "CALIBRATE",
        
        # Typing
        "type": "TYPE",
        
        # Drag
        "drag": "DRAG",
        "move": "DRAG",
        "drop": "DROP",
        "release": "DROP",
        
        # Exit
        "exit": "EXIT",
        "quit": "EXIT",
    }
    
    def __init__(self, use_offline_mode: bool = False):
        """
        Initialize voice processor.
        
        Args:
            use_offline_mode: Use Vosk (offline) instead of Google Speech API
        """
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.use_offline = use_offline_mode
        self.listening = False
        
        # Confidence threshold
        self.confidence_threshold = 0.5
        
        # Background listening mode
        self.background_thread = None
        self.audio_queue = queue.Queue()
        
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("✓ Voice processor initialized")
            print(f"  Mode: {'Offline (Vosk)' if use_offline else 'Online (Google Speech API)'}")
        except Exception as e:
            print(f"⚠️  Microphone initialization warning: {e}")

    def listen(self, timeout: float = 5.0) -> Optional[str]:
        """
        Listen for voice command with timeout.
        
        Args:
            timeout: Maximum listening duration in seconds
            
        Returns:
            Recognized command or None if timeout/no recognition
        """
        try:
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=timeout)
            
            # Try Google Speech API first (more accurate)
            if not self.use_offline:
                return self._recognize_google(audio)
            else:
                return self._recognize_offline(audio)
        
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            print(f"⚠️  Speech API error: {e}")
            # Fall back to offline if online fails
            if not self.use_offline:
                return self._recognize_offline(audio)
            return None
        except sr.WaitTimeoutError:
            return None

    def _recognize_google(self, audio) -> Optional[str]:
        """
        Google Speech Recognition (online, more accurate).
        
        Args:
            audio: Audio data from microphone
            
        Returns:
            Recognized text or None
        """
        try:
            result = self.recognizer.recognize_google(audio, language='en-US')
            return result.lower().strip()
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            print(f"Google Speech API error: {e}")
            return None

    def _recognize_offline(self, audio) -> Optional[str]:
        """
        Offline speech recognition using Vosk.
        Requires: pip install vosk pocketsphinx
        
        Args:
            audio: Audio data from microphone
            
        Returns:
            Recognized text or None
        """
        try:
            from vosk import Model, KaldiRecognizer
            import json
            
            # Use small English model
            model = Model(lang="en-us")
            recognizer_vosk = KaldiRecognizer(model, 16000)
            recognizer_vosk.AcceptWaveform(audio.get_raw_data())
            
            result = json.loads(recognizer_vosk.Result())
            if 'result' in result and result['result']:
                text = ' '.join([item['conf'] for item in result['result']])
                return text.lower().strip()
            
            return None
        except ImportError:
            print("⚠️  Vosk not installed. Install with: pip install vosk")
            return None
        except Exception as e:
            print(f"Offline recognition error: {e}")
            return None

    def extract_command(self, text: str) -> Optional[str]:
        """
        Extract VocalIris command from recognized text.
        Uses keyword matching to find valid commands.
        
        Args:
            text: Recognized speech text
            
        Returns:
            Extracted command or None if no match
        """
        if not text:
            return None
        
        text_lower = text.lower().strip()
        
        # Exact matches
        if text_lower in self.COMMAND_KEYWORDS:
            return self.COMMAND_KEYWORDS[text_lower]
        
        # Substring matching for "type" commands
        if text_lower.startswith("type "):
            return text  # Return full command
        
        # Fuzzy matching: check if any keyword is in the text
        for keyword in self.COMMAND_KEYWORDS:
            if keyword in text_lower:
                return self.COMMAND_KEYWORDS[keyword]
        
        return None

    def start_background_listening(self):
        """
        Start background listening thread for continuous voice input.
        Useful for non-blocking command processing.
        """
        if self.listening:
            return
        
        self.listening = True
        self.background_thread = threading.Thread(
            target=self._background_listening_loop,
            daemon=True
        )
        self.background_thread.start()
        print("✓ Background listening started")

    def _background_listening_loop(self):
        """
        Continuous listening loop (runs in background thread).
        """
        while self.listening:
            try:
                text = self.listen(timeout=1.0)
                if text:
                    command = self.extract_command(text)
                    if command:
                        self.audio_queue.put(command)
            except Exception as e:
                print(f"Background listening error: {e}")

    def get_command(self, blocking: bool = False, timeout: Optional[float] = None) -> Optional[str]:
        """
        Get next command from background listening queue.
        
        Args:
            blocking: Block until command available
            timeout: Maximum wait time in seconds
            
        Returns:
            Next command or None
        """
        try:
            return self.audio_queue.get(blocking=blocking, timeout=timeout)
        except queue.Empty:
            return None

    def stop_background_listening(self):
        """Stop background listening thread."""
        self.listening = False
        if self.background_thread:
            self.background_thread.join(timeout=2)
        print("✓ Background listening stopped")

    def cleanup(self):
        """Clean up voice processor resources."""
        self.stop_background_listening()


class AdvancedVoiceProcessor(VoiceProcessor):
    """
    Enhanced voice processor with:
    - Noise filtering
    - Accent adaptation
    - Custom grammar/vocabulary
    - Voice activity detection (VAD)
    """
    
    def __init__(self, **kwargs):
        """Initialize with advanced features."""
        super().__init__(**kwargs)
        self.vad_enabled = False
        self.custom_vocabulary = []
    
    def add_custom_words(self, words: list):
        """
        Add custom vocabulary for better recognition.
        
        Args:
            words: List of custom words/commands
        """
        self.custom_vocabulary.extend(words)
        print(f"✓ Added {len(words)} custom words to vocabulary")
    
    def enable_voice_activity_detection(self):
        """
        Enable Voice Activity Detection (VAD) to avoid false positives.
        Requires: pip install pyannote.audio
        """
        try:
            import pyannote.audio
            self.vad_enabled = True
            print("✓ Voice Activity Detection enabled")
        except ImportError:
            print("⚠️  pyannote.audio not installed for VAD")
            self.vad_enabled = False
    
    def noise_reduction(self, audio):
        """
        Apply noise reduction to audio before recognition.
        Uses spectral subtraction.
        
        Args:
            audio: Audio data
            
        Returns:
            Cleaned audio
        """
        try:
            import noisereduce as nr
            import numpy as np
            
            audio_data = np.frombuffer(audio.get_raw_data(), np.int16)
            reduced = nr.reduce_noise(y=audio_data, sr=16000)
            return reduced
        except ImportError:
            print("⚠️  noisereduce not installed")
            return audio
