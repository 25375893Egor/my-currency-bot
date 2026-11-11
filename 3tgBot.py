import telebot
from telebot import types
import requests
import re

TOKEN = "9041389245:AAG6NETPQuO-e-9prXf3m5voJN9qXNHsGXg"
bot = telebot.TeleBot(TOKEN)

# Функция получения курсов
def get_rates():
    try:
        url = "https://open.er-api.com/v6/latest/RUB"
        response = requests.get(url, timeout=5)
        data = response.json()
        return data['rates']['USD'], data['rates']['CNY']
    except Exception as e:
        print(f"Ошибка при получении курса: {e}")
        return None, None

# Меню с кнопками
@bot.message_handler(commands=['start'])
def start_message(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_usd = types.InlineKeyboardButton("🇺🇸 USD", callback_data='conv_USD')
    btn_cny = types.InlineKeyboardButton("🇨🇳 CNY", callback_data='conv_CNY')
    btn_rub = types.InlineKeyboardButton("🇷🇺 RUB", callback_data='conv_RUB')
    markup.add(btn_usd, btn_cny, btn_rub)
    
    bot.send_message(message.chat.id, "Привет! Выбери валюту, которую хочешь перевести (бот покажет результат сразу во всех трех):", reply_markup=markup)

# Ловим нажатия на кнопки
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data.startswith('conv_'):
        # Вытаскиваем название валюты из данных кнопки (USD, CNY или RUB)
        base_currency = call.data.split('_')[1]
        msg = bot.send_message(call.message.chat.id, f"Введи сумму в {base_currency} (только цифры):")
        # Передаем валюту в следующую функцию
        bot.register_next_step_handler(msg, process_conversion, base_currency)

# ЕДИНАЯ ФУНКЦИЯ для расчета всех трех валют
def process_conversion(message, base_currency):
    try:
        # Пытаемся превратить текст в число (если ввели запятую, меняем на точку)
        amount = float(message.text.replace(',', '.'))
        
        usd_rate, cny_rate = get_rates()
        if usd_rate is None:
            bot.send_message(message.chat.id, "Ошибка сети. Не удалось получить курс.")
            return

        # Сначала переводим всё в РУБЛИ (базовая валюта)
        if base_currency == 'USD':
            rub_amount = amount / usd_rate
        elif base_currency == 'CNY':
            rub_amount = amount / cny_rate
        else:
            rub_amount = amount

        # Теперь из рублей считаем остальные две
        final_usd = round(rub_amount * usd_rate, 2)
        final_cny = round(rub_amount * cny_rate, 2)
        final_rub = round(rub_amount, 2)

        # Формируем красивый ответ
        response = (
            f"💵 Твоя сумма: {amount} {base_currency}\n\n"
            f"🇷🇺 Рубли: {final_rub} RUB\n"
            f"🇺🇸 Доллары: {final_usd} USD\n"
            f"🇨🇳 Юани: {final_cny} CNY"
        )
        bot.send_message(message.chat.id, response)
        
    except ValueError:
        bot.send_message(message.chat.id, "Ошибка! Нужно ввести просто число, без букв (например, 100 или 50.5).")

# Старый добрый текстовый обработчик (если писать вручную)
@bot.message_handler(content_types=['text'])
def echo_message(message):
    text = message.text.lower()
    match = re.search(r'(\d+(?:\.\d+)?)\s*(usd|доллар|cny|юань|rub|руб)', text)
    
    if match:
        amount = float(match.group(1))
        currency = match.group(2)
        usd_rate, cny_rate = get_rates()
        
        # Тут логика точно такая же, как в кнопках
        if currency in ['rub', 'руб']:
            rub = amount
        elif currency in ['usd', 'доллар']:
            rub = amount / usd_rate
        else:
            rub = amount / cny_rate
            
        bot.send_message(message.chat.id, 
            f"💵 Сумма: {amount} {currency.upper()}\n\n"
            f"🇷🇺 Рубли: {round(rub, 2)} RUB\n"
            f"🇺🇸 Доллары: {round(rub * usd_rate, 2)} USD\n"
            f"🇨🇳 Юани: {round(rub * cny_rate, 2)} CNY"
        )
    else:
        bot.send_message(message.chat.id, f"Ты написал: {message.text}")

print("Бот с тройной конвертацией запущен...")
bot.infinity_polling()
