import telebot
from telebot import types
from main import load_config, load_translation, parse_float_input
import yaml
from log import log_decorator
from db_operations import set_user_language, update_user_language, check_user_exists, get_user_language, register_user
from models import Transaction
from db_operations import add_record_to_db, get_expense_entries, get_income_entries, add_financial_entry ,get_financial_entry_by_name, get_all_transactions_by_user_id
from db_operations import get_user_session_state, update_user_session_state, start_user_session, get_financial_entry_by_telegram_id
from db_operations import get_financial_entries_by_type
from reports import general_report, category_report, monthly_report, plot_report
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
from datetime import datetime
from func import (bot_token,
                  user_amounts,
                  generate_operations_keyboard,
                  load_language_pack,
                  load_translation,
                  lang_keyboard,
                  generate_regular_keyboard,
                  )
calendar = DetailedTelegramCalendar()



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
        bot.send_message(user_id, greeting, reply_markup = generate_regular_keyboard())

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
    user_id = message.chat.id
    lang_code = get_user_language(user_id)
    language_pack = load_language_pack(lang_code)
    markup = generate_regular_keyboard()
    help_text = f"{language_pack['help']['title']}\n\n"
    help_text += f"{language_pack['help']['description']}\n\n"
    for command, description in language_pack['help']['commands'].items():
        help_text += f"{command} - {description}\n"
    help_text += f"\n{language_pack['help']['note']}"
    
    bot.send_message(user_id, help_text, reply_markup = markup)

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
    user_id = call.message.chat.id
    language = call.data.split('_')[1]  # Извлечение языка из callback_data 
    if not set_user_language(user_id, language):  # Смена языка в чате
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
    else:
            error_msg = load_translation("error", language)
            bot.answer_callback_query(call.id, error_msg)

# ====== управление статьями доходов и расходов

@bot.message_handler(commands=['add_entry'])
def add_entry_command(message):
    start_user_session(message.chat.id, "ADDING_ENTRY_NAME")
    bot.reply_to(message, load_translation("choose_category", get_user_language(message.from_user.id)))

@bot.message_handler(func=lambda message: get_user_session_state(message.chat.id) == "ADDING_ENTRY_NAME", content_types=['text'])
def get_entry_name(message):
    user_entry_name = message.text
    # Сохраняем название статьи во временном хранилище или базе данных
    # Здесь я использую глобальный словарь для простоты
    user_amounts[message.chat.id] = {"entry_name": user_entry_name}
    update_user_session_state(message.chat.id, "ADDING_ENTRY_TYPE")
    markup = generate_operations_keyboard("entry_edit", get_user_language(message.from_user.id), message.from_user.id)
    bot.send_message(message.chat.id, load_translation("category_name", get_user_language(message.from_user.id)), reply_markup=markup)

@bot.callback_query_handler(func=lambda call: get_user_session_state(call.message.chat.id) == "ADDING_ENTRY_TYPE" and call.data in ["expense_entry", "income_entry"])
def handle_entry_type(call):
    entry_name = user_amounts[call.message.chat.id]["entry_name"]
    user_id = call.message.chat.id
    user_lang = get_user_language(user_id)
    if call.data == "expense_entry":
        add_financial_entry(entry_name, True, user_id)
        bot.send_message(user_id, f"{load_translation('category_added', user_lang )} '{entry_name}' {load_translation('added_success', user_lang )}")
    elif call.data == "income_entry":
        add_financial_entry(entry_name, False, user_id)
        bot.send_message(user_id, f"{load_translation('category_added', user_lang )} '{entry_name}' {load_translation('added_success', user_lang )}")
    # Удаляем временные данные и возвращаемся в начальное состояние
    del user_amounts[call.message.chat.id]
    update_user_session_state(call.message.chat.id, "START")

@bot.message_handler(func=lambda message: any(char.isdigit() for char in message.text))
@log_decorator
def handle_number_input(message):
    # Попытка преобразовать введенный текст в float
    try:
        amount = parse_float_input(message.text)
    except ValueError:
        bot.send_message(message.chat.id, "Ошибка! Неверный формат суммы.")
        return

    user_amounts[message.from_user.id] = amount
    start_user_session(message.chat.id, "ADDING_TRANSACTION")
    entries = get_financial_entry_by_telegram_id(message.from_user.id)
    bot.reply_to(message, load_translation("add_transaction", get_user_language(message.from_user.id)), reply_markup=generate_operations_keyboard("income_expense", load_language_pack(get_user_language(message.from_user.id)), message.from_user.id))


@bot.callback_query_handler(func=lambda call: (call.data.startswith('expense_save') or call.data.startswith('income_save')) and get_user_session_state(call.message.chat.id) == "ADDING_TRANSACTION")
@log_decorator
def record_transaction(call):
    user_id = call.from_user.id
    user_language = get_user_language(user_id)

    if call.data in ["expense_save", "income_save"]:
        transaction_type = "expense" if call.data == "expense_save" else "income"
        markup_type = 'fin_entry_expense' if transaction_type == "expense" else 'fin_entry_income'
        markup = generate_operations_keyboard(markup_type, user_language, user_id)
        bot.reply_to(call.message, load_translation("choose_category", user_language), reply_markup=markup)
        return

    amount = user_amounts.pop(user_id, None)
    if not amount:
        bot.send_message(call.message.chat.id, "Ошибка! Сумма не найдена.")
        return

    try:
        amount_float = float(amount)
        if "expense" in call.data:
            amount_float = -amount_float
    except ValueError:
        bot.send_message(call.message.chat.id, "Ошибка! Неверный формат суммы.")
        return

    entry_id = call.data.split('_')[-1]
    print(call.data, entry_id)
    transaction = Transaction(user_id=user_id, amount=amount_float, entry_id=entry_id)
    add_record_to_db(transaction)

    bot.send_message(call.message.chat.id, load_translation("amount_added", user_language))
    update_user_session_state(call.message.chat.id, "START")


# отчеты

@bot.callback_query_handler(func=lambda call: call.data.startswith("year_"))
def handle_year_selection(call):
    year = int(call.data.split("_")[1])
    monthly_data = monthly_report(call.from_user.id, year)
    report_msg = "Доходы/расходы по месяцам:\n"
    for month, amount in monthly_data.items():
        report_msg += f"{month}: {amount}\n"
    bot.send_message(call.message.chat.id, report_msg)

@bot.message_handler(commands=['get_report'])
def get_report_command(message):
    bot.send_message(message.chat.id, load_translation("get_reports", get_user_language(message.from_user.id)), reply_markup=generate_operations_keyboard("reports", get_user_language(message.from_user.id), message.from_user.id))

@bot.callback_query_handler(func=lambda call: call.data in ['general_report', 'category_report', 'monthly_report', 'plot_report', 'monthly_report1'])
def handle_report_request(call):
    user_id = call.message.chat.id
    
    if call.data == 'general_report':
        income, expense = general_report(user_id)
        bot.send_message(user_id, f"Общий доход: {income}\nОбщий расход: {expense}")

    elif call.data == 'category_report':
        income_by_category, expense_by_category = category_report(user_id)
        report_msg = "Доходы по категориям:\n"
        for category, amount in income_by_category.items():
            report_msg += f"{category}: {amount}\n"
        report_msg += "\nРасходы по категориям:\n"
        for category, amount in expense_by_category.items():
            report_msg += f"{category}: {amount}\n"
        bot.send_message(user_id, report_msg)
    elif call.data == 'monthly_report':
        markup = generate_operations_keyboard("monthly_report1", get_user_language(user_id), user_id)
        bot.send_message(call.message.chat.id, "Пожалуйста, выберите год для отчета:", reply_markup=markup)
        print(call.data)
        monthly_data = monthly_report(user_id, 2023)  # Пример для 2023 года
        total_income, total_expense = monthly_report(user_id, 2023)
        
        report_message = f"Ваши расходы: {total_expense}\nВаши доходы: {total_income}\n Итого: {total_income+total_expense}"
        print(report_message)

        bot.send_message(user_id, report_message)

    elif call.data == 'plot_report':
        # Для графика мы можем использовать данные из категориального отчета или месячного отчета
        income_by_category, _ = category_report(user_id)
        plot_report(income_by_category, "Доходы по категориям", "Категория", "Сумма")
        bot.send_message(user_id, "График доходов по категориям отправлен.")


if __name__ == "__main__":
    bot.polling(none_stop=True)
