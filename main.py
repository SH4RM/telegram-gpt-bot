import os
import json
import openai
from flask import Flask, request
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4o"

openai.api_key = OPENAI_API_KEY
app = Flask(__name__)
HISTORY_PATH = 'history.json'

def load_history(chat_id):
    if not os.path.exists(HISTORY_PATH):
        return []
    with open(HISTORY_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get(str(chat_id), [])

def save_history(chat_id, history):
    if os.path.exists(HISTORY_PATH):
        with open(HISTORY_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {}

    data[str(chat_id)] = history
    with open(HISTORY_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    requests.post(url, json=payload)

def ask_gpt(history):
    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=history
    )
    return response.choices[0].message.content

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    if 'message' not in data:
        return 'ok'
    message = data['message']
    chat_id = message['chat']['id']
    text = message.get('text')

    if not text:
        send_message(chat_id, "Я понимаю только текст.")
        return 'ok'

    history = load_history(chat_id)
    history.append({"role": "user", "content": text})

    try:
        reply = ask_gpt(history)
    except Exception as e:
        reply = f"Ошибка: {e}"
        send_message(chat_id, reply)
        return 'ok'

    history.append({"role": "assistant", "content": reply})
    save_history(chat_id, history)
    send_message(chat_id, reply)
    return 'ok'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
