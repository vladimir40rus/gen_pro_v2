from .user_repo import UserRepo, get_user_repo
from .article_repo import ArticleRepo, get_article_repo
from .tag_repo import TagRepo, get_tag_repo
from .favorite_repo import FavoriteRepo, get_favorite_repo
from .comment_repo import CommentRepo, get_comment_repo
from .follower_repo import FollowerRepo, get_follower_repo

__all__ = [
    "UserRepo",
    "get_user_repo",
    "ArticleRepo",
    "get_article_repo",
    "TagRepo",
    "get_tag_repo",
    "FavoriteRepo",
    "get_favorite_repo",
    "CommentRepo",
    "get_comment_repo",
    "FollowerRepo",
    "get_follower_repo",
]