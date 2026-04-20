from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database import get_db
from app.models import Article, User, Tag, ArticleTag, Favorite
from app.schemas.article import ArticleCreate, ArticleUpdate, ArticleResponse
from app.schemas.wrappers import ArticleResponseWrapper, ArticlesResponseWrapper

router = APIRouter(prefix="/articles", tags=["Articles"])


@router.post("/", response_model=ArticleResponseWrapper, summary="Создание новой статьи")
async def create_article(article_data: ArticleCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(Article).where(Article.slug == article_data.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Slug already exists")

    user_result = await db.execute(select(User).limit(1))
    author = user_result.scalar_one_or_none()
    if not author:
        raise HTTPException(400, "No users found. Create a user first.")

    article = Article(
        title=article_data.title,
        description=article_data.description or "",
        body=article_data.body,
        slug=article_data.slug,
        author_id=author.id
    )

    db.add(article)
    await db.commit()
    await db.refresh(article)

    if article_data.tags:
        for tag_name in article_data.tags:
            tag_result = await db.execute(select(Tag).where(Tag.tag == tag_name))
            tag = tag_result.scalar_one_or_none()
            if not tag:
                tag = Tag(tag=tag_name)
                db.add(tag)
                await db.flush()

            article_tag = ArticleTag(article_id=article.id, tag_id=tag.id)
            db.add(article_tag)
        await db.commit()

    article_response = ArticleResponse(
        id=article.id,
        title=article.title,
        description=article.description,
        body=article.body,
        slug=article.slug,
        author=author,
        tags=article_data.tags or [],
        favorited=False,
        favorites_count=0,
        comments_count=0,
        created_at=article.created_at,
        updated_at=article.updated_at
    )

    return ArticleResponseWrapper(article=article_response.model_dump())


@router.get("/", response_model=ArticlesResponseWrapper, summary="Получение списка статей")
async def list_articles(
        skip: int = Query(0, ge=0),
        limit: int = Query(20, ge=1, le=100),
        tag: Optional[str] = Query(None),
        author: Optional[str] = Query(None),
        favorited: Optional[str] = Query(None),
        user_id: Optional[int] = Query(None),
        db: AsyncSession = Depends(get_db)
):
    query = select(Article)

    if author:
        author_result = await db.execute(select(User).where(User.username == author))
        author_user = author_result.scalar_one_or_none()
        if author_user:
            query = query.where(Article.author_id == author_user.id)
        else:
            return ArticlesResponseWrapper(articles=[], articles_count=0)

    if tag:
        query = query.join(ArticleTag).join(Tag).where(Tag.tag == tag)

    if favorited:
        user_result = await db.execute(select(User).where(User.username == favorited))
        user = user_result.scalar_one_or_none()
        if user:
            query = query.join(Favorite).where(Favorite.user_id == user.id)
        else:
            return ArticlesResponseWrapper(articles=[], articles_count=0)

    count_query = select(func.count()).select_from(query.subquery())
    total_count_result = await db.execute(count_query)
    total_count = total_count_result.scalar() or 0

    query = query.order_by(desc(Article.created_at)).offset(skip).limit(limit)
    result = await db.execute(query)
    articles = result.scalars().all()

    response_articles = []
    for article in articles:
        author_result = await db.execute(select(User).where(User.id == article.author_id))
        author = author_result.scalar_one()

        tags_result = await db.execute(
            select(Tag.tag)
            .join(ArticleTag, Tag.id == ArticleTag.tag_id)
            .where(ArticleTag.article_id == article.id)
        )
        tags = [row[0] for row in tags_result.all()]

        favorites_count_result = await db.execute(
            select(func.count()).select_from(Favorite).where(Favorite.article_id == article.id)
        )
        favorites_count = favorites_count_result.scalar() or 0

        from app.models import Comment
        comments_count_result = await db.execute(
            select(func.count()).select_from(Comment).where(Comment.article_id == article.id)
        )
        comments_count = comments_count_result.scalar() or 0

        favorited_status = False
        if user_id:
            fav_result = await db.execute(
                select(Favorite).where(
                    Favorite.user_id == user_id,
                    Favorite.article_id == article.id
                )
            )
            favorited_status = fav_result.scalar_one_or_none() is not None

        article_response = ArticleResponse(
            id=article.id,
            title=article.title,
            description=article.description,
            body=article.body,
            slug=article.slug,
            author=author,
            tags=tags,
            favorited=favorited_status,
            favorites_count=favorites_count,
            comments_count=comments_count,
            created_at=article.created_at,
            updated_at=article.updated_at
        )
        response_articles.append(article_response.model_dump())

    return ArticlesResponseWrapper(
        articles=response_articles,
        articles_count=total_count
    )


@router.get("/{slug}", response_model=ArticleResponseWrapper)
async def get_article(
        slug: str,
        user_id: Optional[int] = Query(None),
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Article).where(Article.slug == slug))
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(404, "Article not found")

    author = await db.get(User, article.author_id)

    tags_result = await db.execute(
        select(Tag.tag)
        .join(ArticleTag, Tag.id == ArticleTag.tag_id)
        .where(ArticleTag.article_id == article.id)
    )
    tags = [row[0] for row in tags_result.all()]

    favorites_count_result = await db.execute(
        select(func.count()).select_from(Favorite).where(Favorite.article_id == article.id)
    )
    favorites_count = favorites_count_result.scalar() or 0

    from app.models import Comment
    comments_count_result = await db.execute(
        select(func.count()).select_from(Comment).where(Comment.article_id == article.id)
    )
    comments_count = comments_count_result.scalar() or 0

    favorited = False
    if user_id:
        fav_result = await db.execute(
            select(Favorite).where(
                Favorite.user_id == user_id,
                Favorite.article_id == article.id
            )
        )
        favorited = fav_result.scalar_one_or_none() is not None

    article_response = ArticleResponse(
        id=article.id,
        title=article.title,
        description=article.description,
        body=article.body,
        slug=article.slug,
        author=author,
        tags=tags,
        favorited=favorited,
        favorites_count=favorites_count,
        comments_count=comments_count,
        created_at=article.created_at,
        updated_at=article.updated_at
    )

    return ArticleResponseWrapper(article=article_response.model_dump())


@router.put("/{slug}", response_model=ArticleResponseWrapper)
async def update_article(
        slug: str,
        article_data: ArticleUpdate,
        user_id: Optional[int] = Query(None),
        db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Article).where(Article.slug == slug))
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(404, "Article not found")

    if article_data.title is not None:
        article.title = article_data.title
    if article_data.description is not None:
        article.description = article_data.description
    if article_data.body is not None:
        article.body = article_data.body
    if article_data.slug is not None:
        if article_data.slug != slug:
            existing = await db.execute(select(Article).where(Article.slug == article_data.slug))
            if existing.scalar_one_or_none():
                raise HTTPException(400, "Slug already exists")
        article.slug = article_data.slug

    await db.commit()
    await db.refresh(article)

    author = await db.get(User, article.author_id)

    tags_result = await db.execute(
        select(Tag.tag)
        .join(ArticleTag, Tag.id == ArticleTag.tag_id)
        .where(ArticleTag.article_id == article.id)
    )
    tags = [row[0] for row in tags_result.all()]

    favorites_count_result = await db.execute(
        select(func.count()).select_from(Favorite).where(Favorite.article_id == article.id)
    )
    favorites_count = favorites_count_result.scalar() or 0

    from app.models import Comment
    comments_count_result = await db.execute(
        select(func.count()).select_from(Comment).where(Comment.article_id == article.id)
    )
    comments_count = comments_count_result.scalar() or 0

    favorited = False
    if user_id:
        fav_result = await db.execute(
            select(Favorite).where(
                Favorite.user_id == user_id,
                Favorite.article_id == article.id
            )
        )
        favorited = fav_result.scalar_one_or_none() is not None

    article_response = ArticleResponse(
        id=article.id,
        title=article.title,
        description=article.description,
        body=article.body,
        slug=article.slug,
        author=author,
        tags=tags,
        favorited=favorited,
        favorites_count=favorites_count,
        comments_count=comments_count,
        created_at=article.created_at,
        updated_at=article.updated_at
    )

    return ArticleResponseWrapper(article=article_response.model_dump())


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Article).where(Article.slug == slug))
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(404, "Article not found")

    await db.delete(article)
    await db.commit()