from sqlalchemy import Column, Integer, String, TIMESTAMP, Table, ForeignKey, Index, func
from sqlalchemy.orm import relationship
from app.infra_external.models.base import Base


# Связующая таблица для Many-to-Many (Article <-> Tag)
article_tag_association = Table(
    "article_tags",
    Base.metadata,
    Column("article_id", Integer, ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    Column("created_at", TIMESTAMP, server_default=func.now()),
    Index("idx_article_tags_article", "article_id"),
    Index("idx_article_tags_tag", "tag_id"),
)


class TagDB(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    # Связи
    articles = relationship("ArticleDB", secondary=article_tag_association, back_populates="tags")

    __table_args__ = (
        Index("idx_tags_name", "name"),
    )

    def __repr__(self):
        return f"<Tag(id={self.id}, name={self.name})>"