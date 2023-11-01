import telebot
from telebot import types
from main import load_config, load_translation
import yaml
from log import log_decorator
from db_operations import set_user_language, update_user_language, check_user_exists, get_user_language, register_user
from models import Transaction
from db_operations import add_record_to_db, get_expense_entries, get_income_entries, add_financial_entry ,get_financial_entry_by_name, get_all_transactions_by_user_id
# Загружаем конфигурацию
config = load_config()
bot_token = config['bot_token']

# Глобальное временное хранилище
user_amounts = {}

# загрузка языкового пакета
@log_decorator
def load_language_pack(lang_code):
    """Загружает языковой пакет на основе переданного кода языка."""
    # print(f'выбран язык {lang_code}')
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

#=====операционная клавиатура
@log_decorator
def generate_operations_keyboard(type, language_pack, uid):
    """
    Generate an inline keyboard with financial operations.
    
    Args:
    - language_pack (dict): The language pack containing the translations.
    
    Returns:
    - InlineKeyboardMarkup: The generated keyboard.
    """

    lang_code = get_user_language(uid)
    language_pack = load_language_pack(lang_code)
    # keyboard = generate_operations_keyboard("enter_data", language_pack)
    # print(f'принт из генератора клавы {lang_code}, {language_pack}')
    markup = types.InlineKeyboardMarkup(row_width=2)
    if type == "enter_data":
        
        buttons = [
            types.InlineKeyboardButton(language_pack['record_expense'], callback_data='record_expense'),
            types.InlineKeyboardButton(language_pack['record_income'], callback_data='record_income'),
            types.InlineKeyboardButton(language_pack['financial_entries'], callback_data='financial_entries'),
            types.InlineKeyboardButton(language_pack['get_reports'], callback_data='get_reports')
        ]
    elif type == "income_expense":
        buttons = [
            types.InlineKeyboardButton(language_pack['record_expense'], callback_data='expense_save'),
            types.InlineKeyboardButton(language_pack['record_income'], callback_data='income_save'),
        ] 
    elif type == "fin_entry_expense":
        expense_entries = get_expense_entries(uid)
        buttons = [types.InlineKeyboardButton(entry.name, callback_data=f'expense_save_{entry.id}') for entry in expense_entries]

    elif type == "fin_entry_income":
        income_entries = get_income_entries(uid)
        buttons = [types.InlineKeyboardButton(entry.name, callback_data=f'income_save_{entry.id}') for entry in income_entries]
    elif type == "entry_edit":
        buttons = [
            types.InlineKeyboardButton(load_translation("category_expense", lang_code), callback_data="expense_entry"),
            types.InlineKeyboardButton(load_translation("category_income", lang_code), callback_data="income_entry")
        ]    
    else:
        buttons = [
            types.InlineKeyboardButton(language_pack['record_expense'], callback_data='record_expense'),
            #types.InlineKeyboardButton(language_pack['record_income'], callback_data='record_income'),
            types.InlineKeyboardButton(language_pack['financial_entries'], callback_data='financial_entries'),
            #types.InlineKeyboardButton(language_pack['get_reports'], callback_data='get_reports')
        ]
    markup.add(*buttons)
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
        bot.edit_message_text(chat_id=user_id, message_id=call.message.message_id, text=load_translation("registration_completed", chosen_language))
    else:
        bot.edit_message_text(chat_id=user_id, message_id=call.message.message_id, text=load_translation("error", chosen_language))
          
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
    # print(f'принт из функции change_language_callback{call.data}')
    user_id = call.message.chat.id
    language = call.data.split('_')[1]  # Извлечение языка из callback_data 
    # print(f'полученный язык: {language}')
    if not set_user_language(user_id, language):  # Смена языка в чате
        # print(user_id, language)
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

# ====== управление статьями доходов и расходов

@bot.message_handler(commands=['add_entry'])
def add_entry_command(message):
    markup = generate_operations_keyboard("entry_edit", get_user_language(message.from_user.id), message.from_user.id)
    bot.send_message(message.chat.id, "Введите название статьи и выберите тип:", reply_markup=markup)

# ==== запись статьи в бд

@bot.callback_query_handler(func=lambda call: call.data in ["expense_entry", "income_entry"])
def handle_entry_type(call):
    entry_name = call.message.text.split("Введите название статьи и выберите тип:")[1].strip()
    user_id = call.message.chat.id

    if call.data == "expense_entry":
        # Добавляем статью расхода в базу данных
        add_financial_entry(entry_name, True, user_id)  # True означает, что это расход
        bot.send_message(user_id, f"Статья расхода '{entry_name}' успешно добавлена!")
    elif call.data == "income_entry":
        # Добавляем статью дохода в базу данных
        add_financial_entry(entry_name, False, user_id)  # False означает, что это доход
        bot.send_message(user_id, f"Статья дохода '{entry_name}' успешно добавлена!")

@bot.message_handler(func=lambda message: message.text.isdigit())
@log_decorator
def handle_number_input(message):
    user_amounts[message.from_user.id] = message.text
    bot.send_message(message.chat.id, load_translation(load_translation("choose_category", get_user_language(message.from_user.id)), get_user_language(message.from_user.id)), reply_markup=generate_operations_keyboard("income_expense", load_language_pack(get_user_language(message.from_user.id)), message.from_user.id))

@bot.callback_query_handler(func=lambda call: call.data == 'record_expense')
@log_decorator
def choose_expense_category(call):
    bot.send_message(call.message.chat.id, load_translation("choose_category", get_user_language(message.from_user.id)), reply_markup=generate_operations_keyboard("fin_entry_expense", load_language_pack(get_user_language(call.from_user.id)), call.from_user.id))

@bot.callback_query_handler(func=lambda call: call.data.startswith('expense_save'))
@log_decorator
def record_expense(call):
    print('принт из функции запроса статей')
    amount = user_amounts.pop(call.from_user.id, None)
    if not amount:
        bot.send_message(call.message.chat.id, "Ошибка! Сумма не найдена.")
        return

    try:
        amount_float = float(amount)
    except ValueError:
        bot.send_message(call.message.chat.id, "Ошибка! Неверный формат суммы.")
        return

    entry = get_financial_entry_by_name("expense", call.message.chat.id)
    print(f'/n/n{entry}/n/n')
    if not entry:
        bot.send_message(call.message.chat.id, "Ошибка! Статья не найдена.")
        return

    expense = Transaction(user_id=call.from_user.id, amount=-amount_float, entry=entry)
    add_record_to_db(expense)
    bot.send_message(call.message.chat.id, load_translation("amount_added", get_user_language(call.message.chat.id)))

@bot.callback_query_handler(func=lambda call: call.data.startswith('income_save'))
@log_decorator
def record_income(call):
    amount = user_amounts.pop(call.from_user.id, None)
    if not amount:
        bot.send_message(call.message.chat.id, "Ошибка! Сумма не найдена.")
        return

    try:
        amount_float = float(amount)
    except ValueError:
        bot.send_message(call.message.chat.id, "Ошибка! Неверный формат суммы.")
        return

    entry = get_financial_entry_by_name("income", call.message.chat.id)
    print(f'income: {entry}')
    if not entry:
        bot.send_message(call.message.chat.id, "Ошибка! Статья не найдена.")
        return

    income = Transaction(user_id=call.from_user.id, amount=amount_float, entry=entry)
    add_record_to_db(income)
    bot.send_message(call.message.chat.id, load_translation("amount_added", get_user_language(call.message.chat.id)))


if __name__ == "__main__":
    bot.polling(none_stop=True)
