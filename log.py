import logging
import os
import functools
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime
from main import load_config

#основной логгер====
def setup_logger(name, config):
    """
    Setup logger with given name and configuration.

    Parameters:
    - name: Name of the logger
    - config: Configuration dictionary containing log level, path, and filename

    Returns:
    - logger: Configured logger instance
    """
    # Создание директории для логов, если она не существует
    log_path = config['logging']['path']
    if not os.path.exists(log_path):
        os.makedirs(log_path)

    # Настройка логгера
    logger = logging.getLogger(name)
    log_level = getattr(logging, config['logging']['level'])
    logger.setLevel(log_level)

    # Создание обработчика для записи логов в файл
    log_filename = f"{config['logging']['filename']}_{datetime.now().strftime('%Y-%m-%d')}.log"
    full_log_path = os.path.join(log_path, log_filename)
    file_handler = TimedRotatingFileHandler(full_log_path, when='midnight', backupCount=7)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    # Добавление обработчика к логгеру
    logger.addHandler(file_handler)
    
    return logger

config = load_config()  # Загрузка конфигурации

def log_decorator(func):
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        try:
            logger.info(f"Function '{func.__name__}' started.")
            result = func(*args, **kwargs)
            logger.info(f"Function '{func.__name__}' finished successfully.")
            return result
        except Exception as e:
            logger.error(f"Error in function '{func.__name__}': {str(e)}")
            raise e
    return wrapped

# обычная функция логгера
import logging
from logging.handlers import TimedRotatingFileHandler
import os

# Настройка пути и имени файла журнала
log_path = config.get('db_logging', {}).get('path', 'logs')
log_filename = 'db_operations.log'
full_log_path = os.path.join(log_path, log_filename)

# Создание директории для логов, если она не существует
if not os.path.exists(log_path):
    os.makedirs(log_path)

# Настройка логгера
logger = logging.getLogger('db_operations_logger')
logger.setLevel(logging.INFO)  # Можно изменить уровень логирования при необходимости

# Создание обработчика для записи логов в файл
file_handler = TimedRotatingFileHandler(full_log_path, when='midnight', backupCount=7)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

# Добавление обработчика к логгеру
logger.addHandler(file_handler)