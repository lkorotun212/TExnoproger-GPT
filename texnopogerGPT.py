import telebot
import requests
from openai import OpenAI
from datetime import datetime
import re
import langdetect

bot = telebot.TeleBot('8094647476:AAG-LJ8xPwZ48k4g-L26xyQwAIjflZAUEq4')
alert_bot = telebot.TeleBot('7589135275:AAFmG20JWh6fyfr9pgSK8fUv0RMfhYxukLk')

client = OpenAI(  # 🔧 FIX: ініціалізував клієнта через правильний клас
    api_key="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"
)

NEWS_API_KEY = 'ee58ae79b7174efc8cb97cec9853eb06'
crypto = 'bca9f320-f9fc-410f-8b0c-a9ef74f3dc86'
user_histories = {}
ADMIN_CHAT_ID = 7589135275

client_for_images = OpenAI(api_key="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")

def is_simple_math_expression(text):
    return bool(re.fullmatch(r'\d+\s*[\+\-\*/]\s*\d+', text))

def get_main_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('📡Отримати новини📡', 'Задати питання')
    markup.row('📆Дізнатися дату📆', 'Переглянути історію')
    markup.row('Який зараз курс долара?', 'help')
    markup.row('😓бот не працює!😥', 'Коли ти зроблений')
    return markup

def get_news(query):
    url = f'https://newsapi.org/v2/everything?q={query}&apiKey={NEWS_API_KEY}'
    response = requests.get(url)
    if response.status_code == 200:
        news_data = response.json()
        articles = news_data['articles']
        if articles:
            news_summary = ""
            for article in articles[:5]:
                title = article['title']
                description = article['description']
                url = article['url']
                news_summary += f"**{title}**\n{description}\n{url}\n\n"
            return news_summary
        else:
            return "Немає новин за вашим запитом."
    else:
        return "Помилка при отриманні новин."

def get_usd_to_uah_rate():
    url = f'https://api.exchangerate-api.com/v4/latest/USD'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        uah_rate = data['rates'].get('UAH')
        if uah_rate:
            return f"Курс долара зараз: 1 USD = {uah_rate} UAH"
        else:
            return "Не вдалося знайти курс гривні."
    else:
        return "Помилка при отриманні курсу валют."

def contains_url(text):
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return re.search(url_pattern, text)

def generate_image(prompt_text):
    API_KEY = 'quickstart-QUdJIGlzIGNvbWluZy4uLi4K'  # 🔧 FIX: додав відсутній API_KEY для DeepAI
    headers = {
        'api-key': API_KEY
    }
    data = {
        'text': prompt_text
    }
    response = requests.post('https://api.deepai.org/api/text2img', data=data, headers=headers)
    if response.status_code == 200:
        result = response.json()
        return result.get('output_url')
    else:
        print("Помилка генерації картинки:", response.text)
        return None

@bot.message_handler(commands=['start'])
def start_handler(message):
    first_name = message.from_user.first_name
    bot.send_message(message.chat.id,
                     f'Привіт, {first_name}! Я TechnoProger IA 🤖! Напиши мені будь-яке питання, і я дам відповідь! ✨',
                     reply_markup=get_main_menu())
    user_histories[message.chat.id] = []

@bot.message_handler(func=lambda message: True)
def chat_with_gpt(message):
    user_id = message.chat.id
    user_input = message.text.lower()

    if user_input.startswith('згенерувати картинку'):
        prompt_text = message.text.replace('згенерувати картинку', '').strip()
        if not prompt_text:
            bot.send_message(user_id, "❗ Будь ласка, напишіть опис для картинки після команди.")
            return

        detected_language = langdetect.detect(message.text)
        try:
            translation_completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system",
                     "content": "Translate the following text to English, but don't explain anything."},
                    {"role": "user", "content": prompt_text}
                ]
            )
            english_prompt = translation_completion.choices[0].message.content.strip()
        except Exception as e:
            bot.send_message(user_id, "⚠️ Помилка при перекладі опису для картинки. Спробуйте ще раз.")
            return

        bot.send_message(user_id, "🖌️ Генерую вашу картинку... Це може зайняти до хвилини!")
        image_url = generate_image(english_prompt)
        if image_url:
            caption_text = {
                'uk': f"🖼️ Ось ваша картинка за запитом: \"{prompt_text}\"",
                'ru': f"🖼️ Вот ваша картинка по запросу: \"{prompt_text}\"",
                'en': f"🖼️ Here is your image for the prompt: \"{prompt_text}\""
            }.get(detected_language,
                  f"🖼️ Ось ваша картинка за запитом: \"{prompt_text}\"")
            bot.send_photo(user_id, image_url, caption=caption_text)
        else:
            bot.send_message(user_id,
                             "⚠️ Виникла проблема при генерації картинки. Спробуйте ще раз пізніше або іншим описом.")
        return

    if user_id not in user_histories:
        user_histories[user_id] = []

    if contains_url(user_input):
        bot.send_message(user_id, "⚠️ Вибачте, я не переходжу за посиланнями. Не надсилайте їх мені! 🛑")
        return

    user_histories[user_id].append({"role": "user", "content": user_input})

    try:
        detected_language = langdetect.detect(user_input)
        if 'який сьогодні день' in user_input or 'дізнатися дату' in user_input:
            now = datetime.now()
            formatted_date = now.strftime("%d.%m.%Y")
            formatted_time = now.strftime("%H:%M")
            reply = f"📅 Сьогодні {formatted_date}, 🕒 час: {formatted_time}."
        elif 'коли ти зроблений' in user_input:
            username = "𝕮𝖔𝖑𝖉𝖊𝕮𝖆𝖙"
            reply = f"Я був створений {username} 🧙‍♂️ та запущений 26 квітня 2025 року о 10:00. Моя місія — допомагати вам! 🚀"
        elif 'де тьолки' in user_input:
            reply = "😉 Дівчата можуть бути в різних місцях: у парку 🌳, в кафе ☕, на заходах 🎉 або в університетах 🎓. Будь ввічливим!"
        elif 'новини' in user_input:
            query = user_input.replace('новини', '').strip()
            if query:
                reply = get_news(query)
            else:
                reply = "📰 Будь ласка, уточніть, про які новини ви хочете дізнатися."
        elif 'який зараз курс долара?' in user_input or 'долар' in user_input:
            reply = get_usd_to_uah_rate()
        elif 'help' in user_input:
            reply = "😉Запитайте в мене що не будь я попитаюсь нормально на це відповісти😆"
        elif '😓бот не працює!😥' in user_input:
            username = message.from_user.first_name
            alert_bot.send_message(ADMIN_CHAT_ID, f"🚨 {username} подав скаргу, що бот не працює!")
            reply = "😓 Ми працюємо над вирішенням проблеми. Скоро все буде добре!"
        else:
            try:
                completion = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content":
                            "Ти — універсальний асистент із гарним настроєм 😊.\n\n"
                            f"Відповідай на мові, на якій пише користувач: {detected_language}.\n"
                            "- Якщо користувач задає питання про людей, події або факти, відповідай чітко і ввічливо, додаючи кілька смайликів.\n"
                            "- Якщо користувач пише математичну задачу або вираз, тоді:\n"
                                " * Пиши без LaTeX-символів.\n"
                                " * Вводь змінні через літери.\n"
                                " * Пояснюй рішення крок за кроком простими реченнями.\n"
                                " * Після рішення обов'язково напиши Відповідь: ...\n"
                            "Будь дружелюбним у тоні відповіді 🧡."
                        }
                    ] + user_histories[user_id][-10:]
                )
                reply = completion.choices[0].message.content
            except Exception as e:
                reply = "⚠️ Сталася помилка при відповіді GPT. Спробуйте пізніше."

        bot.send_message(user_id, reply)

    except Exception as e:
        bot.send_message(user_id, "⚠️ Виникла внутрішня помилка. Спробуйте знову.")

print("✅ Бот успішно запущено!")
bot.polling(none_stop=True)
