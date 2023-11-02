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
        # print(file)
    except Exception as e:
        print(f"Error loading language pack for {lang_code}: {e}")
        return None


# ==== клавиатура выбора языка
@log_decorator
def lang_keyboard(cb_param):
    """
    Create and return the language selection keyboard.
    
    Returns:
    - InlineKeyboardMarkup: The created keyboard.
    """
    # print(f'принт из функции клавиатуры {cb_param}')
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
    # print(global_callback)
    lang_code = get_user_language(uid)
    language_pack = load_language_pack(lang_code)
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
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
            types.InlineKeyboardButton(language_pack['category_expense'], callback_data="expense_entry"),
            types.InlineKeyboardButton(language_pack['category_income'], callback_data="income_entry")
        ]    
    elif type == "monthly_reports1":
        current_year = datetime.now().year
        buttons = [types.InlineKeyboardButton(text=str(year), callback_data=f"year_{year}") for year in range(datetime.now().year - 5, datetime.now().year + 1)]
    elif type == "reports":
        buttons = [
            types.InlineKeyboardButton(language_pack['general_report'], callback_data='general_report'),
            types.InlineKeyboardButton(language_pack['report_by_categories'], callback_data='category_report'),
            types.InlineKeyboardButton(language_pack['monthly_report'], callback_data='monthly_report'),
            types.InlineKeyboardButton(language_pack['income_expense_chart'], callback_data='plot_report')
        ]  

    markup.add(*buttons)
    return markup

def generate_regular_keyboard():
    """Generate a regular keyboard with specified commands."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=False)
    buttons = [
        '/add_entry',
        '/change_language',
        '/get_reports',
        '/help'
    ]
    for btn in buttons:
        markup.add(btn)
    return markup