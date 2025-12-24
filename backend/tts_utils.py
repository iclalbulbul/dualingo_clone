from gtts import gTTS
import os
import uuid

def text_to_speech(text: str, lang: str = "en") -> str:
    """
    Verilen metni sese çevirir (mp3).
    Geriye oluşturulan ses dosyasının yolunu döndürür.
    """
    # Ses dosyalarının tutulacağı klasör
    folder = os.path.join("static", "audio")
    os.makedirs(folder, exist_ok=True)

    # Her çağrıda benzersiz dosya adı
    filename = f"tts_{uuid.uuid4().hex}.mp3"
    filepath = os.path.join(folder, filename)

    # gTTS ile mp3 oluştur
    tts = gTTS(text=text, lang=lang)
    tts.save(filepath)

    return filepath
