import telebot
from telebot import types
import requests

TOKEN = '9041389245:AAG6NETPQuO-e-9prXf3m5voJN9qXNHsGXg'
bot = telebot.TeleBot(TOKEN)

# Функция получения курсов (добавили EUR)
def get_rates():
    try:
        url = "https://open.er-api.com/v6/latest/RUB"
        response = requests.get(url, timeout=5)
        data = response.json()
        return data['rates']['USD'], data['rates']['CNY'], data['rates']['EUR']
    except Exception as e:
        print(f"Ошибка при получении курса: {e}")
        return None, None, None

# Список всех наших кнопок для проверки
BUTTONS = ['🇺🇸 USD', '🇨🇳 CNY', '🇪🇺 EUR', '🇷🇺 RUB']

# Команда /start - создает постоянное меню внизу
@bot.message_handler(commands=['start'])
def start_message(message):
    # ReplyKeyboardMarkup создает кнопки, которые НЕ исчезают
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    
    # Создаем кнопки
    btn_usd = types.KeyboardButton('🇺🇸 USD')
    btn_cny = types.KeyboardButton('🇨🇳 CNY')
    btn_eur = types.KeyboardButton('🇪🇺 EUR')
    btn_rub = types.KeyboardButton('🇷🇺 RUB')
    
    # Добавляем их в меню
    markup.add(btn_usd, btn_cny, btn_eur, btn_rub)
    
    bot.send_message(message.chat.id, "Привет! Выбери валюту, которую хочешь перевести (или просто напиши текст, например '100 usd'):", reply_markup=markup)

# Ловим нажатия на постоянные кнопки
@bot.message_handler(func=lambda message: message.text in BUTTONS)
def ask_amount(message):
    # Определяем, какую валюту выбрал пользователь
    base_currency = message.text.split()[-1] # Берет последнее слово (USD, CNY, EUR или RUB)
    
    msg = bot.send_message(message.chat.id, f"Введи сумму в {base_currency} (только цифры):")
    # Передаем валюту в следующую функцию
    bot.register_next_step_handler(msg, process_conversion, base_currency)

# Функция расчета
def process_conversion(message, base_currency):
    # Если пользователь передумал и написал /start
    if message.text == '/start':
        start_message(message)
        return

    # Защита: если пользователь нажал на кнопку вместо ввода цифры
    if message.text in BUTTONS:
        ask_amount(message)
        return

    try:
        amount = float(message.text.replace(',', '.'))
        usd_rate, cny_rate, eur_rate = get_rates()
        
        if usd_rate is None:
            bot.send_message(message.chat.id, "Ошибка сети. Не удалось получить курс.")
            return

        # Переводим в рубли
        if base_currency == 'USD':
            rub_amount = amount / usd_rate
        elif base_currency == 'CNY':
            rub_amount = amount / cny_rate
        elif base_currency == 'EUR':
            rub_amount = amount / eur_rate
        else:
            rub_amount = amount

        # Считаем остальные валюты
        final_usd = round(rub_amount * usd_rate, 2)
        final_cny = round(rub_amount * cny_rate, 2)
        final_eur = round(rub_amount * eur_rate, 2)
        final_rub = round(rub_amount, 2)

        response = (
            f"💵 Твоя сумма: {amount} {base_currency}\n\n"
            f"🇷🇺 Рубли: {final_rub} RUB\n"
            f"🇺🇸 Доллары: {final_usd} USD\n"
            f"🇨🇳 Юани: {final_cny} CNY\n"
            f"🇪🇺 Евро: {final_eur} EUR"
        )
        bot.send_message(message.chat.id, response)
        
    except ValueError:
        bot.send_message(message.chat.id, "Ошибка! Нужно ввести просто число, без букв (например, 100 или 50.5).")

# Если пользователь просто пишет текст (например "100 usd"), работает старый умный поиск
@bot.message_handler(content_types=['text'])
def text_message(message):
    if message.text.startswith('/'):
        return
        
    text = message.text.lower()
    import re
    match = re.search(r'(\d+(?:\.\d+)?)\s*(usd|доллар|cny|юань|rub|руб|eur|евро)', text)
    
    if match:
        amount = float(match.group(1))
        currency = match.group(2)
        usd_rate, cny_rate, eur_rate = get_rates()
        
        if currency in ['rub', 'руб']:
            rub = amount
        elif currency in ['usd', 'доллар']:
            rub = amount / usd_rate
        elif currency in ['cny', 'юань']:
            rub = amount / cny_rate
        elif currency in ['eur', 'евро']:
            rub = amount / eur_rate
            
        bot.send_message(message.chat.id, 
            f"💵 Сумма: {amount} {currency.upper()}\n\n"
            f"🇷🇺 Рубли: {round(rub, 2)} RUB\n"
            f"🇺🇸 Доллары: {round(rub * usd_rate, 2)} USD\n"
            f"🇨🇳 Юани: {round(rub * cny_rate, 2)} CNY\n"
            f"🇪🇺 Евро: {round(rub * eur_rate, 2)} EUR"
        )
    else:
        bot.send_message(message.chat.id, f"Я тебя не понял. Нажми на кнопку внизу или напиши, например: 100 usd")

print("Бот с постоянными кнопками запущен...")
bot.infinity_polling()

