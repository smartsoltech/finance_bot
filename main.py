import os
import yaml
from dotenv import load_dotenv

def load_config():
    # Загрузка переменных окружения из .env файла
    load_dotenv()
    
    # Получение переменных из .env
    env_data = {
        "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_API_TOKEN"),
        "DB_USERNAME": os.getenv("DB_USERNAME"),
        "DB_PASSWORD": os.getenv("DB_PASSWORD")
    }
    
    # Загрузка данных из config.yaml
    with open('config.yaml', 'r') as config_file:
        config_data = yaml.safe_load(config_file)
    
    # Создание строки подключения к базе данных
    if config_data['database']['type']!='sqlite':
        DATABASE_URL = f"{config_data['database']['type']}://{env_data['DB_USERNAME']}:{env_data['DB_PASSWORD']}@/{config_data['database']['path']}{config_data['database']['filename']}"
    else:
        DATABASE_URL = f"{config_data['database']['type']}:///{config_data['database']['path']}/{config_data['database']['filename']}"
    # Объединение данных в единый словарь
    config = {
        "db_url": DATABASE_URL,
        "bot_token": env_data["TELEGRAM_BOT_TOKEN"],
        "default_language": config_data['language']['default'],
        "logging": config_data["logging"],
        "db_logging": config_data["db_logging"]
    }
    
    return config

cfg = load_config()

def load_translation(phrase_key, user_language):
    """
    Load the corresponding translation for a given phrase key and user language.
    
    Args:
    - phrase_key (str): The key for which the translation is needed.
    - user_language (str): User's language preference (e.g., 'en', 'ru').
    
    Returns:
    - str: Translated phrase. If not found, returns an English placeholder.
    """
    try:
        lang_file_path = os.path.join('lang', f"{user_language}.yaml")
        with open(lang_file_path, 'r') as lang_file:
            translations = yaml.safe_load(lang_file)
            print(phrase_key)
            return translations.get(phrase_key, "Translation not found!!!")
    except Exception as e:
       print(f"Error loading translation for key {phrase_key} and language {user_language}: {e}")
    #return "Translation not found!"


if __name__ == "__main__":
    print(cfg)
