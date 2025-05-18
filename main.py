import os
from flask import Flask, request
import openai
from dotenv import load_dotenv
import json

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
client = openai.OpenAI(api_key=OPENAI_API_KEY)

HISTORY_FILE = "history.json"

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    with open(HISTORY_FILE, "r") as f:
        return json.load(f)

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    
    # Получаем ID чата и текст сообщения
    try:
        chat_id = data["message"]["chat"]["id"]
        user_message = data["message"]["text"]
    except KeyError:
        return "No message found", 200

    # Загружаем историю, добавляем новое сообщение
    history = load_history()
    history.append({"role": "user", "content": user_message})

    # Ограничим до последних 10 сообщений (экономия токенов)
    recent_history = history[-10:]

    # Получаем ответ от GPT-4o (или другой выбранной модели)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=recent_history
    )

    assistant_reply = response.choices[0].message.content
    history.append({"role": "assistant", "content": assistant_reply})
    save_history(history)

    # Отправляем ответ обратно в Telegram
    send_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": assistant_reply
    }

    import requests
    requests.post(send_url, json=payload)

    return "OK", 200
