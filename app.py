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


def get_incident_tickets():
    url = "https://dev89134.service-now.com/api/now/table/incident"

    headers = {
        "Accept": "application/json",
        "Authorization": "Basic " + base64.b64encode(f"admin:1/1YRrg^pwKO".encode()).decode()
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            tickets = response.json().get('result', [])
            return tickets
        else:
            logger.error("Error retrieving incident tickets: %s", response.text)
            return []
    except requests.exceptions.RequestException as e:
        logger.error("An error occurred while retrieving incident tickets: %s", str(e))
        return []


def get_incident_ticket(ticket_number):
    url = "https://dev89134.service-now.com/api/now/table/incident"

    headers = {
        "Accept": "application/json",
        "Authorization": "Basic " + base64.b64encode(f"admin:1/1YRrg^pwKO".encode()).decode()
    }

    params = {
        "sysparm_query": f"number={ticket_number}"
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            tickets = response.json().get('result', [])
            if tickets:
                return tickets[0]  # Return the first ticket
            else:
                logger.info("Ticket not found: %s", ticket_number)
                return None
        else:
            logger.error("Error retrieving incident ticket: %s", response.text)
            return None
    except requests.exceptions.RequestException as e:
        logger.error("An error occurred while retrieving incident ticket: %s", str(e))
        return None


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

    def process_user_request(self, user_input):
        if self.wake_up(user_input):
            return "Hello, I am Dave the AI. What can I do for you?"
        elif "time" in user_input:
            return self.action_time()
        elif any(i in user_input for i in ["thank", "thanks"]):
            return np.random.choice(["you're welcome!", "anytime!", "no problem!", "cool!", "I'm here if you need me!", "mention not"])
        elif any(i in user_input for i in ["exit", "close"]):
            return np.random.choice(["Tata", "Have a good day", "Bye", "Goodbye", "Hope to meet soon", "peace out!"])
        elif any(i in user_input for i in ["incident", "tickets"]):
            ticket_number = extract_ticket_number(user_input)
            if ticket_number:
                ticket = get_incident_ticket(ticket_number)
                if ticket:
                    return f"Ticket ID: {ticket.get('number')}, Description: {ticket.get('short_description')}, Status: {ticket.get('state')}"
                else:
                    return f"Ticket not found for number: {ticket_number}"
            else:
                return "Please provide a valid ticket number."
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


def extract_ticket_number(text):
    pattern = r'INC\d{7}'
    ticket_number = re.search(pattern, text)
    if ticket_number:
        return ticket_number.group()
    else:
        return None


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
