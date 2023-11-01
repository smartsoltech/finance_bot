from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)  # Telegram user ID
    language = Column(String(5))  # e.g., 'en', 'ru'
    first_name = Column(String(100))  # User's first name
    last_name = Column(String(100))  # User's last name
    uid = Column(String(50))  # Unique Telegram ID for the user
    transactions = relationship("Transaction", back_populates="user")
    session = relationship("UserSession", uselist=False, back_populates="user")
    financial_entries = relationship("FinancialEntry", back_populates="user")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    amount = Column(Float)
    entry_id = Column(Integer, ForeignKey('financial_entries.id'))
    date = Column(DateTime, default=datetime.datetime.utcnow)
    user = relationship("User", back_populates="transactions")
    entry = relationship("FinancialEntry")

class FinancialEntry(Base):
    __tablename__ = "financial_entries"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    is_expense = Column(Boolean, default=True)
    user_id = Column(Integer, ForeignKey('users.id'))  # Добавляем поле user_id
    transactions = relationship("Transaction", back_populates="entry")
    user = relationship("User", back_populates="financial_entries")  # Добавляем отношение с моделью User


class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)
    current_state = Column(String, default="START")
    user = relationship("User", back_populates="session")
