from sqlalchemy import Column, Integer, String, TIMESTAMP, func
from sqlalchemy.orm import relationship
from app.infra_external.models.base import Base


class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(30), nullable=False, unique=True)
    email = Column(String(100), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    bio = Column(String(500), nullable=True)
    image_url = Column(String(500), nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=True, onupdate=func.now())

    # Связи
    articles = relationship("ArticleDB", back_populates="author", cascade="all, delete-orphan")
    comments = relationship("CommentDB", back_populates="author", cascade="all, delete-orphan")
    favorites = relationship("FavoriteDB", back_populates="user", cascade="all, delete-orphan")
    followers = relationship("FollowerDB", foreign_keys="FollowerDB.follower_id", back_populates="follower")
    following = relationship("FollowerDB", foreign_keys="FollowerDB.following_id", back_populates="following")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"