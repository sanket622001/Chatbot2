from flask import Flask, render_template, request, jsonify
import speech_recognition as sr
from gtts import gTTS
import transformers
import playsound
import os
import time
import datetime
import numpy as np
import logging
import requests
import base64
import re

app = Flask(__name__)
logger = logging.getLogger(__name__)


class ChatBot():
    def __init__(self, name):
        self.name = name

    def speech_to_text(self, audio):
        recognizer = sr.Recognizer()
        try:
            self.text = recognizer.recognize_google(audio)
            print("Me  --> ", self.text)
        except Exception as e:
            logger.exception("Error in speech-to-text conversion")
            raise e

    @staticmethod
    def text_to_speech(text):
        print("Dev --> ", text)
        try:
            speaker = gTTS(text=text, lang="en")
            filename = 'res.mp3'
            speaker.save(filename)
            playsound.playsound(filename)
            os.remove(filename)
        except Exception as e:
            logger.exception("Error in text-to-speech conversion")
            raise e

    def wake_up(self, text):
        return True if self.name in text.lower() else False

    @staticmethod
    def action_time():
        return datetime.datetime.now().time().strftime('%H:%M')

    @staticmethod
    def extract_ticket_number(text):
        match = re.search(r'\b([A-Za-z]+\d+)\b', text)
        if match:
            return match.group(1)
        else:
            return None

    @staticmethod
    def get_incident_ticket(ticket_number):
        url = f"https://dev89134.service-now.com/api/now/table/incident?number={ticket_number}"

        headers = {
            "Content-Type": "application/json",
            "Authorization": "Basic " + base64.b64encode(f"admin:1/1YRrg^pwKO".encode()).decode()
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raise an exception for non-2xx status codes
            ticket = response.json().get('result')
            return ticket
        except requests.exceptions.RequestException as e:
            logger.error("An error occurred while retrieving incident ticket: %s", str(e))
            return None

    def process_user_request(self, user_input):
        if self.wake_up(user_input) is True:
            return "Hello, I am Dave the AI. What can I do for you?"
        elif "time" in user_input:
            return self.action_time()
        elif any(i in user_input for i in ["thank", "thanks"]):
            return np.random.choice(["you're welcome!", "anytime!", "no problem!", "cool!", "I'm here if you need me!", "mention not"])
        elif any(i in user_input for i in ["exit", "close"]):
            return np.random.choice(["Tata", "Have a good day", "Bye", "Goodbye", "Hope to meet soon", "peace out!"])
        elif any(i in user_input for i in ["incident", "tickets"]):
            ticket_number = self.extract_ticket_number(user_input)
            if ticket_number:
                ticket_info = self.get_incident_ticket(ticket_number)
                if ticket_info:
                    return f"Ticket ID: {ticket_info.get('number')}, Description: {ticket_info.get('short_description')}, Status: {ticket_info.get('state')}"
                else:
                    return f"Ticket {ticket_number} not found."
            else:
                return "No ticket number found in the input."
        else:
            if user_input == "ERROR":
                return "Sorry, come again?"
            else:
                chat = nlp(transformers.Conversation(user_input), pad_token_id=50256)
                response = str(chat)
                response = response[response.find("bot >> ") + 6:].strip()
                return response


ai = ChatBot(name="dev")
nlp = transformers.pipeline("conversational", model="microsoft/DialoGPT-medium")
os.environ["TOKENIZERS_PARALLELISM"] = "true"


@app.route('/', methods=['GET', 'POST'])
def chat():
    if request.method == 'POST':
        data = request.get_json()
        message = data['message']

        try:
            ai.text = message

            response = ai.process_user_request(ai.text)

            ai.text_to_speech(response)
            return jsonify({'response': response})
        except Exception as e:
            logger.exception("Error in processing user request")
            return jsonify({'error': 'An error occurred. Please try again later.'}), 500

    return render_template('index.html')


@app.route('/speak', methods=['GET'])
def speak():
    text = request.args.get('text')
    ai.text_to_speech(text)
    return ''


if __name__ == '__main__':
    app.run()
