import pandas as pd
import matplotlib.pyplot as plt
from db_operations import get_all_transactions_by_user_id
from log import log_decorator

@log_decorator
def general_report(user_id, start_date=None, end_date=None):
    transactions = get_all_transactions_by_user_id(user_id)

    # Извлекаем атрибуты из каждого объекта Transaction
    data = [{'user_id': t.user_id, 'amount': t.amount, 'entry_id': t.entry_id} for t in transactions]
    print(data)
    # Преобразуем список словарей в DataFrame
    df = pd.DataFrame(data)

    if 'amount' in df.columns:
        total_income = df[df['amount'] > 0]['amount'].sum()
        total_expense = df[df['amount'] < 0]['amount'].sum()
    else:
        print("The 'amount' column is missing in the DataFrame.")
        total_income = 0  # or some default value
    print(total_income)
    return total_income, total_expense

@log_decorator
def category_report(user_id, start_date=None, end_date=None):
    transactions = get_all_transactions_by_user_id(user_id)
    
    df = pd.DataFrame(transactions)
    
        # Извлекаем атрибуты из каждого объекта Transaction
    data = [{'user_id': t.user_id, 'amount': t.amount, 'entry_id': t.entry_id} for t in transactions]
    
    income_by_category = df[df['amount'] > 0].groupby('entry_id')['amount'].sum()
    expense_by_category = df[df['amount'] < 0].groupby('entry_id')['amount'].sum()

    return income_by_category, expense_by_category

@log_decorator
def monthly_report(user_id, year):
    transactions = get_all_transactions_by_user_id(user_id)
    
    # Извлекаем атрибуты из каждого объекта Transaction
    data = [{'user_id': t.user_id, 'amount': t.amount, 'entry_id': t.entry_id, 'date': t.date} for t in transactions]
    print(data)
    
    # Создаем DataFrame из списка словарей
    df = pd.DataFrame(data)
    
    df['month'] = pd.to_datetime(df['date']).dt.month
    
    # Разделяем доходы и расходы
    total_income = df[df['amount'] > 0]['amount'].sum()
    total_expense = df[df['amount'] < 0]['amount'].sum()

    return total_income, total_expense


@log_decorator
def plot_report(data, title, xlabel, ylabel):
    data.plot(kind='bar', figsize=(10, 6))
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.show()

