from speech_stt import listen_and_recognize

def main():
    print("STT testi başlıyor...")
    result = listen_and_recognize()
    print("Sonuç:", result)

if __name__ == "__main__":
    main()
