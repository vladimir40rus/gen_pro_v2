from sqlalchemy import Column, Integer, TIMESTAMP, ForeignKey, Index, func
from sqlalchemy.orm import relationship
from app.infra_external.models.base import Base


class FavoriteDB(Base):
    __tablename__ = "favorites"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    # Связи
    user = relationship("UserDB", back_populates="favorites")
    article = relationship("ArticleDB", back_populates="favorites")

    __table_args__ = (
        Index("idx_favorites_user_id", "user_id"),
        Index("idx_favorites_article_id", "article_id"),
    )

    def __repr__(self):
        return f"<Favorite(user_id={self.user_id}, article_id={self.article_id})>"