from speech_utils import TextToSpeech

def main():
    print("TTS testi başlıyor...")

    tts = TextToSpeech()

    word = "apple"
    kelimeler = [
        f"The correct pronunciation of the word is {word}",
        "Hello",
        "How are you?"
    ]
    for i in kelimeler:
        tts.speak(text=i)

    # 🔥 BÜTÜN METİNLERİ OKUTAN KISIM

    print("TTS testi bitti.")

if __name__ == "__main__":
    main()
