from flask import Flask, render_template, request, jsonify
import speech_recognition as sr
from gtts import gTTS
import transformers
import os
import datetime
import numpy as np
from playsound import playsound

app = Flask(__name__)


class ChatBot():
    def __init__(self, name):
        self.name = name

    def speech_to_text(self, audio):
        recognizer = sr.Recognizer()
        try:
            self.text = recognizer.recognize_google(audio)
            print("Me  --> ", self.text)
        except:
            print("Me  -->  ERROR")

    @staticmethod
    def text_to_speech(text):
        print("Dev --> ", text)
        speaker = gTTS(text=text, lang="en")

        filename = 'res.mp3'
        speaker.save(filename)
        playsound(filename)
        os.remove(filename)

    def wake_up(self, text):
        return True if self.name in text.lower() else False

    @staticmethod
    def action_time():
        return datetime.datetime.now().time().strftime('%H:%M')


ai = ChatBot(name="dev")
nlp = transformers.pipeline("conversational", model="microsoft/DialoGPT-medium")
os.environ["TOKENIZERS_PARALLELISM"] = "true"


@app.route('/', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        message = request.form['text']
        ai.text = message

        if ai.wake_up(ai.text) is True:
            res = "Hello, I am Dave the AI. What can I do for you?"
        elif "time" in ai.text:
            res = ai.action_time()
        elif any(i in ai.text for i in ["thank", "thanks"]):
            res = np.random.choice(
                ["you're welcome!", "anytime!", "no problem!", "cool!", "I'm here if you need me!", "mention not"])
        elif any(i in ai.text for i in ["exit", "close"]):
            res = np.random.choice(["Tata", "Have a good day", "Bye", "Goodbye", "Hope to meet soon", "peace out!"])
        else:
            if ai.text == "ERROR":
                res = "Sorry, come again?"
            else:
                chat = nlp(transformers.Conversation(ai.text), pad_token_id=50256)
                res = str(chat)
                res = res[res.find("bot >> ") + 6:].strip()

        ai.text_to_speech(res)
        return jsonify({'response': res})

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug="True")
