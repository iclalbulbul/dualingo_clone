import speech_recognition as sr


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
