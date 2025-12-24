import pyttsx3

engine = pyttsx3.init()
engine.setProperty("rate", 150)
engine.setProperty("volume", 1.0)

def speak_text(text: str):
    engine.say(text)
    engine.runAndWait()   # ✅ her cümleden sonra hemen okut
