import pyttsx4
import threading


class TextToSpeech:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(TextToSpeech, cls).__new__(cls)
                    cls._instance._init_engine()
        return cls._instance

    def _init_engine(self):
        self.engine = pyttsx4.init()
        self.engine.setProperty("rate", 150)
        self.engine.setProperty("volume", 1.0)
        self._is_speaking = False

    def speak(self, text: str):
        if not text:
            return

        if self._is_speaking:
            return

        self._is_speaking = True
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        finally:
            self._is_speaking = False