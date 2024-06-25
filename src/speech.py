import speech_recognition as sr
import utils

class Lang:
    EN = "en-US"
    JP = "ja-JP"
    FR = "fr-FR"
    ID = "id-ID"
    TH = "th-TH"
    CN = "zh-CN"
    langs = [("English", EN),
             ("Japanese", JP),
             ("French", FR),
             ("Indonesian", ID),
             ("Thai", TH),
             ("Chinese", CN)]

class SpeechToText:
    def __init__(self, lang=Lang.EN):
        self.lang = lang

        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.microphone_stream = self.microphone.__enter__()

    def __del__(self):
        self.microphone_stream.__exit__(None, None, None)

    def set_lang(self, lang):
        self.lang = lang

    def listen(self):
        try:
            audio_data = self.recognizer.listen(self.microphone_stream, timeout=5)
            text = self.recognizer.recognize_google(audio_data, language=self.lang)
            return text
        except:
            return None

    def adjust(self):
        utils.debug("Starting microphone adjustment")
        self.recognizer.adjust_for_ambient_noise(self.microphone_stream)
        utils.debug("End of microphone adjustment")
