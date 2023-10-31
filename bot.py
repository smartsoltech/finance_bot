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

# ==== клавиатура выбора языка
@log_decorator
def lang_keyboard(cb_param):
    """
    Create and return the language selection keyboard.
    
    Returns:
    - InlineKeyboardMarkup: The created keyboard.
    """
    print(f'принт из функции клавиатуры {cb_param}')
    markup = types.InlineKeyboardMarkup(row_width=2)  # Set row_width to 2 for a more organized layout
    buttons = [
        types.InlineKeyboardButton('🇺🇸 English', callback_data=f'{cb_param}_en'),
        types.InlineKeyboardButton('🇷🇺 Русский', callback_data=f'{cb_param}_ru'),
        types.InlineKeyboardButton('🇰🇷 한국어', callback_data=f'{cb_param}_ko'),
        types.InlineKeyboardButton('🇺🇿 O\'zbek', callback_data=f'{cb_param}_uz'),
        types.InlineKeyboardButton('🇰🇿 Қазақша', callback_data=f'{cb_param}_kz')
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
        bot.send_message(user_id, "Choose your language / Выберите ваш язык:", reply_markup=lang_keyboard("register"))
    else:
        user_language = get_user_language(user_id)  # Assuming you have a function to get user's preferred language
        greeting = load_translation("greetings", user_language)
        bot.send_message(user_id, greeting)

@bot.callback_query_handler(func=lambda call: call.data.startswith('register_'))
@log_decorator
def register_bot_user(call):
    user_id = call.message.chat.id
    first_name = call.message.chat.first_name
    last_name = call.message.chat.last_name or ''  # Некоторые пользователи могут не иметь фамилии в профиле.
    uid = str(user_id)  # Здесь мы используем ID пользователя как uid. Вы можете заменить это на свой метод генерации uid.
    
    # Извлекаем язык из callback данных:
    chosen_language = call.data.split('_')[1]

    registered_user = register_user(user_id, chosen_language, first_name, last_name, uid)
    if registered_user:
        bot.edit_message_text(chat_id=user_id, message_id=call.message.message_id, text="You have been successfully registered!")
    else:
        bot.edit_message_text(chat_id=user_id, message_id=call.message.message_id, text="Error registering. Please try again later.")
          
# Команда помощи
@bot.message_handler(commands=['help'])
def send_help(message):
    # Здесь вы можете добавить инструкции по использованию вашего бота.
    bot.send_message(message.chat.id, "This is a financial management bot...")


# ====== смена языка для зареганных юзеров
@bot.message_handler(commands=['change_language'])
@log_decorator
def change_language_command(message):
    user_id = message.chat.id
    user_language = get_user_language(user_id)

    if check_user_exists(user_id):  # Проверка регистрации
        msg = load_translation("choose_language", user_language)
        bot.send_message(user_id, msg, reply_markup=lang_keyboard('change lang'))
    else:
        msg = load_translation("please_register_first", user_language)
        bot.send_message(user_id, msg)

@bot.callback_query_handler(func=lambda call: call.data.startswith('change lang'))
@log_decorator
def change_language_callback(call):
    print(f'принт из функции change_language_callback{call.data}')
    user_id = call.message.chat.id
    language = call.data.split('_')[1]  # Извлечение языка из callback_data 
    print(f'полученный язык: {language}')
    if not set_user_language(user_id, language):  # Смена языка в чате
        print(user_id, language)
        update_user_language(user_id, language) # смена языка в бд
        # провекрка на смену языка
        if get_user_language(user_id) == language:
            success_msg = load_translation("language_changed", language)
            bot.answer_callback_query(call.id, success_msg)
            welcome_msg = load_translation("welcome", language)
            bot.send_message(call.message.chat.id, welcome_msg)
        else:
            error_msg = load_translation("error", language)
            bot.answer_callback_query(call.id, error_msg)
            print(f'1')
    else:
            error_msg = load_translation("error", language)
            bot.answer_callback_query(call.id, error_msg)
            print(f'2')
        
if __name__ == "__main__":
    bot.polling(none_stop=True)
