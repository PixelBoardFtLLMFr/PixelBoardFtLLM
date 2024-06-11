import speech_recognition as sr

class SpeechToText:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.microphone_stream = self.microphone.__enter__()
        self.recognizer.adjust_for_ambient_noise(self.microphone_stream)
    
    def __del__(self):
        self.microphone_stream.__exit__(None, None, None)

    def listen(self):
        try:
            audio_data = self.recognizer.listen(self.microphone_stream)
            text = self.recognizer.recognize_google(audio_data, language='id-ID')
            return text
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            return None