from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, Index, func
from sqlalchemy.orm import relationship
from app.infra_external.models.base import Base


class ArticleDB(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    slug = Column(String(100), nullable=False, unique=True)
    title = Column(String(100), nullable=False)
    description = Column(String(255), nullable=False)
    body = Column(String(500), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=True, onupdate=func.now())

    # Связи
    author = relationship("UserDB", back_populates="articles")
    comments = relationship("CommentDB", back_populates="article", cascade="all, delete-orphan")
    tags = relationship("TagDB", secondary="article_tags", back_populates="articles")
    favorites = relationship("FavoriteDB", back_populates="article", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_articles_author_id", "author_id"),
        Index("idx_articles_slug", "slug"),
        Index("idx_articles_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<Article(id={self.id}, slug={self.slug}, title={self.title})>"