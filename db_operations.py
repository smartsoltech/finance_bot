from main import load_config
from sqlalchemy import create_engine, exc, inspect
from log import log_decorator, setup_logger
from models import User, Transaction, FinancialEntry, Base
from sqlalchemy.orm import sessionmaker

@log_decorator
def ensure_db_and_tables_exist(config):
    DATABASE_URL = config['db_url']
    engine = create_engine(DATABASE_URL)

    # Проверка подключения к базе данных
    try:
        connection = engine.connect()
        connection.close()
        print("Connection to the database was successful!")
    except exc.SQLAlchemyError:
        print("Failed to connect to the database. Please check your connection string.")
        return None

    inspector = inspect(engine)
    
    if not inspector.has_table('users') or \
       not inspector.has_table('finentries') or \
       not inspector.has_table('transactions'):
        # Создаем таблицы, если их нет
        Base.metadata.create_all(engine)
        print("Database tables were created.")
    else:
        print("Database tables already exist.")

    return engine
# Вы можете использовать ваш словарь при вызове функции:
config = {'db_url': 'sqlite:///db/finance.db', 'bot_token': None, 'default_language': 'en'}
engine = ensure_db_and_tables_exist(config)
Session = sessionmaker(bind=engine)


@log_decorator
def set_user_language(user_id, language):
    """
    Update the language preference for a specific user.

    Parameters:
    - user_id: Telegram user ID
    - language: Language code (e.g., 'en', 'ru')

    Returns:
    None
    """
    session = Session()
    

# Настройка логгера
    logger = setup_logger("db_operations_logger", load_config())
    try:
        user = session.query(User).filter(User.telegram_id == user_id).first()
        
        if user:
            user.language = language
            session.commit()
            logger.info(f"Language for user {user_id} set to {language}")
        else:
            logger.warning(f"User with ID {user_id} not found in the database.")
    except Exception as e:
        logger.error(f"Error setting language for user {user_id}: {e}")
    finally:
        session.close()
        
        
#=============== main operations functions==============

@log_decorator
def add_record_to_db(record):
    """Добавление записи в базу данных."""
    session = Session()
    try:
        session.add(record)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

@log_decorator
def get_user_by_telegram_id(telegram_id):
    """Получение пользователя по ID в Telegram."""
    session = Session()
    user = session.query(User).filter_by(telegram_id=telegram_id).first()
    session.close()
    return user

@log_decorator
def get_all_transactions_by_user_id(user_id):
    """Получение всех транзакций пользователя по его ID."""
    session = Session()
    transactions = session.query(Transaction).filter_by(user_id=user_id).all()
    session.close()
    return transactions

@log_decorator
def get_financial_entry_by_id(entry_id):
    """Получение статьи расхода или дохода по ID."""
    session = Session()
    entry = session.query(FinancialEntry).get(entry_id)
    session.close()
    return entry

@log_decorator
def update_user_language(telegram_id, language):
    """Обновление языка пользователя."""
    session = Session()
    try:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if user:
            user.language = language
            session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

# работа с пользовательскими сессиями
@log_decorator
def start_user_session(telegram_id, initial_state="START"):
    """
    Начать новую сессию или обновить текущую для пользователя.
    
    :param telegram_id: ID пользователя в Telegram.
    :type telegram_id: int
    :param initial_state: Начальное состояние сессии.
    :type initial_state: str
    """
    session = Session()
    try:
        user = get_user_by_telegram_id(telegram_id)
        user_session = session.query(UserSession).filter_by(user_id=user.id).first()
        
        if not user_session:
            user_session = UserSession(user_id=user.id, current_state=initial_state)
            session.add(user_session)
        else:
            user_session.current_state = initial_state
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

@log_decorator
def get_user_session_state(telegram_id):
    """
    Получение текущего состояния сессии пользователя.
    
    :param telegram_id: ID пользователя в Telegram.
    :type telegram_id: int
    :return: Текущее состояние сессии.
    :rtype: str
    """
    session = Session()
    user = get_user_by_telegram_id(telegram_id)
    state = session.query(UserSession).filter_by(user_id=user.id).first().current_state
    session.close()
    return state

@log_decorator
def update_user_session_state(telegram_id, new_state):
    """
    Обновление состояния сессии пользователя.
    
    :param telegram_id: ID пользователя в Telegram.
    :type telegram_id: int
    :param new_state: Новое состояние сессии.
    :type new_state: str
    """
    session = Session()
    try:
        user = get_user_by_telegram_id(telegram_id)
        user_session = session.query(UserSession).filter_by(user_id=user.id).first()
        user_session.current_state = new_state
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

#======= операции с пользователями
def check_user_exists(user_id):
    """
    Check if a user exists in the database.
    
    Args:
    - user_id (int): The user's Telegram ID.
    
    Returns:
    - bool: True if the user exists, False otherwise.
    """
    session = Session()
    user = session.query(User).filter_by(id=user_id).first()
    session.close()
    return bool(user)


def register_user(user_id, language='en'):
    """
    Register a new user in the database.
    
    Args:
    - user_id (int): The user's Telegram ID.
    - language (str): The user's preferred language. Default is 'en'.
    
    Returns:
    - User: The created user object.
    """
    session = Session()
    new_user = User(id=user_id, language=language, fist_name, last_name, uid)
    session.add(new_user)
    session.commit()
    session.close()
    return new_user


def get_user_language(user_id):
    """
    Fetch the preferred language of a user from the database.
    
    Args:
    - user_id (int): Telegram user ID.
    
    Returns:
    - str: Language code (e.g., 'en', 'ru'). Returns None if not found.
    """
    try:
        session = Session()
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            return user.language
        return None
    except Exception as e:
        logger.error(f"Error fetching language for user {user_id}: {e}")
        return None
    finally:
        session.close()