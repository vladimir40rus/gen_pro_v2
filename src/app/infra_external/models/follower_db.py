from sqlalchemy import Column, Integer, TIMESTAMP, ForeignKey, Index, CheckConstraint, func
from sqlalchemy.orm import relationship
from app.infra_external.models.base import Base


class FollowerDB(Base):
    __tablename__ = "followers"

    follower_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    following_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())

    # Связи
    follower = relationship("UserDB", foreign_keys=[follower_id], back_populates="followers")
    following = relationship("UserDB", foreign_keys=[following_id], back_populates="following")

    __table_args__ = (
        CheckConstraint("follower_id != following_id", name="check_not_self_follow"),
        Index("idx_followers_follower_id", "follower_id"),
        Index("idx_followers_following_id", "following_id"),
    )

    def __repr__(self):
        return f"<Follower(follower_id={self.follower_id}, following_id={self.following_id})>"