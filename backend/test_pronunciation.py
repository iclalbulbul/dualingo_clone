from speech_stt import listen_and_recognize
from ai_utils import pronunciation_feedback
from speech_utils import TextToSpeech

def main():
    expected_word = "apple"

    print("🎧 Lütfen şu kelimeyi söyleyin:", expected_word)
    recognized = listen_and_recognize(language="en-US")

    result = pronunciation_feedback(expected_word, recognized)

    print("🎯 Puan:", result["score"])
    # print("📝 Geri Bildirim:", result["feedback_tr"])
    
    tts = TextToSpeech()
    tts.speak("eueueueueu çoook içten gonuuşşşşttuuuu")
    


if __name__ == "__main__":
    main()
