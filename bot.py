import telebot
from telebot import types
from main import load_config, load_translation
import yaml
from log import log_decorator
from db_operations import set_user_language, update_user_language, check_user_exists, get_user_language, register_user

# Загружаем конфигурацию
config = load_config()
bot_token = config['bot_token']

# загрузка языкового пакета
@log_decorator
def load_language_pack(lang_code):
    """Загружает языковой пакет на основе переданного кода языка."""
    print(f'выбран язык {lang_code}')
    try:
        with open(f'lang/{lang_code}.yaml', 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
        print(file)
    except Exception as e:
        print(f"Error loading language pack for {lang_code}: {e}")
        return None
# Инициализация бота
bot = telebot.TeleBot(bot_token)


# ==== клавиатура выбора языка
@log_decorator
def lang_keyboard():
    """
    Create and return the language selection keyboard.
    
    Returns:
    - InlineKeyboardMarkup: The created keyboard.
    """
    markup = types.InlineKeyboardMarkup(row_width=2)  # Set row_width to 2 for a more organized layout
    buttons = [
        types.InlineKeyboardButton('🇺🇸 English', callback_data='en'),
        types.InlineKeyboardButton('🇷🇺 Русский', callback_data='ru'),
        types.InlineKeyboardButton('🇰🇷 한국어', callback_data='ko'),
        types.InlineKeyboardButton('🇺🇿 O\'zbek', callback_data='uz'),
        types.InlineKeyboardButton('🇰🇿 Қазақша', callback_data='kz')
    ]
    markup.add(*buttons)  # Unpacking the list to add all buttons
    return markup

# Стартовая команда

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    if not check_user_exists(user_id):
        # If user is not registered, offer registration
        bot.send_message(user_id, "Looks like you're not registered. Let's start with choosing your language:")
        bot.send_message(user_id, "Choose your language / Выберите ваш язык:", reply_markup=lang_keyboard())
    else:
        user_language = get_user_language(user_id)  # Assuming you have a function to get user's preferred language
        greeting = load_translation("greetings", user_language)
        bot.send_message(user_id, greeting)
@bot.callback_query_handler(func=lambda call: call.data == 'register')
def register_bot_user(call):
    user_id = call.message.chat.id
    register_user(user_id)
    bot.edit_message_text(chat_id=user_id, message_id=call.message.message_id, text="You have been successfully registered!")
# @bot.message_handler(commands=['start'])
# def send_welcome(message):
#     markup = types.InlineKeyboardMarkup()
#     itembtn1 = types.InlineKeyboardButton('🇺🇸 English', callback_data='en')
#     itembtn2 = types.InlineKeyboardButton('🇷🇺 Русский', callback_data='ru')
#     itembtn3 = types.InlineKeyboardButton('🇰🇷 한국어', callback_data='ko')
#     itembtn4 = types.InlineKeyboardButton('🇺🇿 O\'zbek', callback_data='uz')
#     itembtn5 = types.InlineKeyboardButton('🇰🇿 Қазақша', callback_data='kz')
#     markup.add(itembtn1, itembtn2, itembtn3, itembtn4, itembtn5)
    
#     bot.send_message(message.chat.id, "Choose your language / Выберите ваш язык:", reply_markup=markup)

# Команда помощи
@bot.message_handler(commands=['help'])
def send_help(message):
    # Здесь вы можете добавить инструкции по использованию вашего бота.
    bot.send_message(message.chat.id, "This is a financial management bot...")

@log_decorator
@bot.callback_query_handler(func=lambda call: call.data in ['en', 'ru', 'ko', 'uz', 'kz'])
def set_language(call):
    # Устанавливаем язык пользователя в базе данных
    set_user_language(call.message.chat.id, call.data)
    
    # Загружаем языковой пакет на основе выбранного языка
    lang_package = load_language_pack(call.data)
    
    if lang_package:
        bot.answer_callback_query(call.id, lang_package['language_set'])
        bot.send_message(call.message.chat.id, lang_package['set_language'])
        bot.send_message(call.message.chat.id, f"{lang_package['welcome']}, {call.from_user.first_name}. {lang_package['greetings']}", parse_mode="HTML")

    else:
        bot.answer_callback_query(call.id, "Error!")
        
if __name__ == "__main__":
    bot.polling(none_stop=True)
