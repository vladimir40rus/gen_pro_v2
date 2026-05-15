from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, Index, func
from sqlalchemy.orm import relationship
from app.infra_external.models.base import Base


class CommentDB(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    body = Column(String(1000), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=True, onupdate=func.now())

    # Связи
    article = relationship("ArticleDB", back_populates="comments")
    author = relationship("UserDB", back_populates="comments")

    __table_args__ = (
        Index("idx_comments_article_id", "article_id"),
        Index("idx_comments_author_id", "author_id"),
        Index("idx_comments_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<Comment(id={self.id}, article_id={self.article_id}, author_id={self.author_id})>"