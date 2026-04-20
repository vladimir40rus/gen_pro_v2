from sqlalchemy import Column, Integer, String, TIMESTAMP, func, ForeignKey, VARCHAR, Index, CheckConstraint
from app.database import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(30), nullable=False)
    email = Column(String(30), nullable=False)
    password_hash = Column(String(255), nullable=False)
    bio = Column(String(500), nullable=True)
    image_url = Column(String(500), nullable=True)  # ← image_url, не image
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=True, onupdate=func.now())

"""ARTICLE"""
class Article(Base):
    __tablename__ = 'article'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    author_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    slug = Column(VARCHAR(50), nullable=False)
    title = Column(VARCHAR(50), nullable=False)
    description = Column(VARCHAR(500), nullable=False) # описание
    body = Column(VARCHAR(500), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=True, onupdate=func.now())
    Index('idx_article_author_id', 'author_id')  # Поиск всех статей автора


"""COMMENT"""
class Comment(Base):
    __tablename__ = 'comment'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    article_id = Column(Integer, ForeignKey('article.id', ondelete='CASCADE'), nullable=False)
    author_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    body = Column(VARCHAR(500), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=True, onupdate=func.now())
    Index('idx_comment_article_id', 'article_id') # Для показа комментариев к статье
    Index('idx_comment_author_id', 'author_id') # Для показа всех комментариев пользователя


"""FAVORITE"""
class Favorite(Base):
    __tablename__ = 'favorite'
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True, nullable=False) # "Identifying Relationship" (идентифицирующая связь). Поле может быть одновременно и первичным ключом (PRIMARY KEY), и внешним ключом (FOREIGN KEY).
    article_id = Column(Integer, ForeignKey('article.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    Index('idx_favorite_article_id', 'article_id') # Для поиска всех, кто лайкнул статью



"""ARTICLE_TAG"""
class ArticleTag(Base):
    __tablename__ = 'article_tag'
    article_id = Column(Integer, ForeignKey('article.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    tag_id = Column(Integer, ForeignKey('tag.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    Index('idx_article_tag_id', 'article_id') # Для поиска всех тегов статьи
    Index('idx_article_tag_tag_id', 'tag_id') # Для поиска всех статей по тегу




"""TAG"""
class Tag(Base):
    __tablename__ = 'tag'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    tag = Column(VARCHAR(50), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())


"""FOLLOWER"""
class Follower(Base):
    __tablename__ = 'follower'
    # составной первичный ключ
    follower_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True,  nullable=False)
    following_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True,  nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    # Чтобы не подписаться на самого себя
    __table_args__ = (
        CheckConstraint('follower_id != following_id', name='following_id_check'),
    )
    Index('idx_follower_following_id', 'follower_id') # Для поиска подписчиков пользователя
