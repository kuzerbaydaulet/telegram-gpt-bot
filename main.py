import telebot
import os
from dotenv import load_dotenv
from openai import OpenAI

import base64
import requests
from PIL import Image
from io import BytesIO

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

bot = telebot.TeleBot(BOT_TOKEN)
client = OpenAI(api_key=OPENAI_API_KEY)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id,f"Привет, {message.from_user.first_name} {message.from_user.last_name}! | Напиши любой запрос.")

@bot.message_handler(commands=['help'])
def send_welcome(message):
    bot.send_message(message.chat.id,"Я бот с ChatGPT. Просто напиши сообщение — я отвечу.", parse_mode='HTML')


# def echo_message(message):
    # bot.send_message(message.chat.id,message.text, parse_mode='HTML')

@bot.message_handler(func = lambda message: True)
def chat_with_gpt(message):
    try:
        response = client.chat.completions.create(
            model = 'gpt-4o-mini',
            messages = [
                {"role":"system", "content": "Ты ассистент, который проверяет домашнее задание"},
                {"role":"user", "content": message.text}
            ]
        )

        answer = response.choices[0].message.content
        bot.send_message(message.chat.id, answer, parse_mode='HTML')

    except Exception as e:
        bot.send_message(message.chat.id, "Ошибка при обращении к ИИ")
        print(e)


@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    try:
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"

        # скачиваем фото
        original_bytes = requests.get(file_url).content

        # 🔥 СЖИМАЕМ
        compressed_bytes = compress_image(original_bytes)

        # base64
        image_base64 = base64.b64encode(compressed_bytes).decode("utf-8")

        user_text = message.caption or "Проверь домашнее задание. Если есть ошибки, распиши по пунктам. Предложи правильное решение"

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_text},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ]
        )

        answer = response.choices[0].message.content
        bot.send_message(message.chat.id, answer)

    except Exception as e:
        bot.send_message(message.chat.id, "Ошибка обработки изображения")
        print(e)


def compress_image(image_bytes, max_size=1024, quality=70):
    img = Image.open(BytesIO(image_bytes))

    # приводим к RGB (важно для PNG/WEBP)
    if img.mode != "RGB":
        img = img.convert("RGB")

    # уменьшаем, сохраняя пропорции
    img.thumbnail((max_size, max_size))

    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=quality, optimize=True)

    return buffer.getvalue()


bot.infinity_polling()