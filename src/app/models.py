from sqlalchemy import Column, Integer, String, TIMESTAMP, func
from app.database import Base

class User(Base):
    __tablename__ = 'users'  # Имя таблицы

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(30), nullable=False)
    email = Column(String(30), nullable=False)
    password_hash = Column(String(20), nullable=False)  # Рекомендую увеличить до 255
    bio = Column(String(500), nullable=True)
    image_url = Column(String(500), nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=True, onupdate=func.now())