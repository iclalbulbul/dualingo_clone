import speech_recognition as sr
import io
import tempfile
import os


def listen_and_recognize(language="en-US") -> str:
    """
    Mikrofonu açar, kullanıcının sesini dinler ve metne çevirir.
    """
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("🎤 Konuşabilirsiniz...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio, language=language)
        print("📝 Algılanan metin:", text)
        return text

    except sr.UnknownValueError:
        return "❌ Ses anlaşılamadı"

    except sr.RequestError:
        return "❌ STT servisine ulaşılamıyor"


def recognize_from_audio_file(audio_file, language="en-US") -> str:
    """
    Web'den gelen ses dosyasını alır ve metne çevirir.
    audio_file: Flask request.files'dan gelen dosya veya dosya yolu
    """
    recognizer = sr.Recognizer()
    
    try:
        # Geçici dosya oluştur
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_path = temp_file.name
            
            # Dosyayı kaydet
            if hasattr(audio_file, 'save'):
                # Flask FileStorage objesi
                audio_file.save(temp_path)
            elif hasattr(audio_file, 'read'):
                # File-like object
                temp_file.write(audio_file.read())
            else:
                # Dosya yolu
                temp_path = audio_file
        
        # Ses dosyasını oku
        with sr.AudioFile(temp_path) as source:
            audio = recognizer.record(source)
        
        # Google STT ile tanı
        text = recognizer.recognize_google(audio, language=language)
        print(f"📝 Web STT Sonuç: {text}")
        
        # Geçici dosyayı sil
        if temp_path != audio_file and os.path.exists(temp_path):
            os.remove(temp_path)
        
        return text
        
    except sr.UnknownValueError:
        return "❌ Ses anlaşılamadı"
    except sr.RequestError as e:
        return f"❌ STT servisine ulaşılamıyor: {e}"
    except Exception as e:
        return f"❌ Ses işleme hatası: {e}"


def recognize_from_blob(audio_blob: bytes, language="en-US") -> str:
    """
    Web'den gelen raw audio blob'u alır ve metne çevirir.
    """
    recognizer = sr.Recognizer()
    
    try:
        # Geçici dosyaya yaz
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(audio_blob)
            temp_path = temp_file.name
        
        # Ses dosyasını oku
        with sr.AudioFile(temp_path) as source:
            audio = recognizer.record(source)
        
        # Google STT ile tanı
        text = recognizer.recognize_google(audio, language=language)
        print(f"📝 Blob STT Sonuç: {text}")
        
        # Temizle
        os.remove(temp_path)
        
        return text
        
    except sr.UnknownValueError:
        return "❌ Ses anlaşılamadı"
    except sr.RequestError as e:
        return f"❌ STT servisine ulaşılamıyor: {e}"
    except Exception as e:
        return f"❌ Ses işleme hatası: {e}"
