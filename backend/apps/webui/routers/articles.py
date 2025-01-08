import logging
import aiohttp
from fastapi import HTTPException, status, APIRouter, Depends
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask
from typing import List, Optional
from pydantic import BaseModel, HttpUrl

from apps.webui.models.articles import (
    Article_Table,
    ArticleModel,
    InsertNewArticleForm,
    BulkInsertNewArticleForm,
)
import json
from apps.webui.models.articles import ArticleResponse, ManyArticlesByIDs
from utils.utils import get_verified_user, get_admin_user, get_current_user
from apps.webui.models.series import Series_Table
from constants import ERROR_MESSAGES
from config import SRC_LOG_LEVELS

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])

router = APIRouter()


class ArticleUrlRequest(BaseModel):
    url: HttpUrl


class ArticleForm(BaseModel):
    article: dict


class ArticleStepsForm(BaseModel):
    step: dict
    step_index: int


################
# GetArticles
################


@router.get("/")
async def get_articles(skip: int = 0, limit: int = 50):
    articles = Article_Table.get_articles(skip=skip, limit=limit)
    return articles


################
# GetArticlesBySeriesId
################


@router.get("/series/{series_id}", response_model=List[ArticleModel])
async def get_articles_by_series_id(series_id: str):
    return Article_Table.get_articles_by_series_id(series_id)


################
# GetArticleById
################


@router.get("/{id}", response_model=Optional[ArticleModel])
async def get_article_by_id(id: str):
    article = Article_Table.get_article_by_id(id)

    if article:
        return article
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.ARTICLE_ATTR_NOT_FOUND("id"),
        )


################
# GetArticleByDocumentId
################


@router.get("/document/{document_id}", response_model=Optional[ArticleModel])
async def get_article_by_document_id(document_id: str, user=Depends(get_verified_user)):
    article = Article_Table.get_article_by_document_id(document_id)
    if article:
        return article
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.ARTICLE_ATTR_NOT_FOUND("document id"),
        )


################
# GetArticleByUrl
################


@router.post("/url", response_model=Optional[ArticleModel])
async def get_article_by_url(request: ArticleUrlRequest):
    article = Article_Table.get_article_by_url(str(request.url))
    if article:
        return article
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.ARTICLE_ATTR_NOT_FOUND("url"),
        )


################
# GetArticlesByUser
################


@router.get("/user/{user_id}", response_model=List[ArticleModel])
async def get_articles_by_user(user_id: str, user=Depends(get_current_user)):
    if user:
        if user_id == user.id:
            return Article_Table.get_articles_by_user_id(user_id)
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ERROR_MESSAGES.ACTION_PROHIBITED,
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.ACTION_PROHIBITED,
        )


################
# GetManyArticlesByIds
################


@router.post("/many", response_model=List[ArticleModel])
async def get_many_articles_by_ids(form_data: ManyArticlesByIDs):
    articles = Article_Table.get_many_articles_by_ids(form_data.ids)
    return articles


################
# AddNewArticle
################

import uuid


def is_valid_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except ValueError:
        return False


@router.post("/add", response_model=Optional[ArticleResponse])
async def add_new_article(form_data: InsertNewArticleForm):

    article = Article_Table.insert_new_article(
        id=form_data.id,
        title=form_data.title,
        document_id=form_data.document_id,
        url=form_data.url,
        category=form_data.category,
        objective=form_data.objective,
        introduction=form_data.introduction,
        applicable_devices=form_data.applicable_devices,
        steps=form_data.steps,
        revision_history=form_data.revision_history,
        series_id=form_data.series_id,
        published=form_data.published,
        user_id=form_data.user_id,
        sources=form_data.sources,
    )

    if article:
        log.debug(f"Article: {article.title}")
        return ArticleResponse(
            **{
                **article.model_dump(),
                "sources": json.loads(article.sources if article.sources else "[]"),
            }
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.DEFAULT(),
        )


################
# BulkAddNewArticle
################


@router.post("/add/bulk", response_model=Optional[List[ArticleModel]])
async def bulk_add_new_article(form_data: BulkInsertNewArticleForm):
    articles: List[ArticleModel] = []
    for article_form in form_data.articles:
        series = Series_Table.get_series_by_name(article_form.series_name)

        if not series:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ERROR_MESSAGES.SERIES_NOT_FOUND,
            )
        article_data = {
            "title": article_form.title,
            "document_id": article_form.document_id,
            "url": article_form.url,
            "category": article_form.category,
            "objective": article_form.objective,
            "introduction": article_form.introduction,
            "applicable_devices": article_form.applicable_devices,
            "steps": article_form.steps,
            "series_id": series.id,
        }
        article = Article_Table.insert_new_article(**article_data)

        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ERROR_MESSAGES.DEFAULT(),
            )
        articles.append(article)

    return articles


################
# UpdateArticle
################


@router.put("/{id}", response_model=Optional[ArticleResponse])
async def update_article_by_id(
    id: str, form_data: ArticleForm, user=Depends(get_verified_user)
):
    article = Article_Table.get_article_by_id(id)
    log.debug(f"Article: {article.title}")
    if article:
        updated = {**article.model_dump(), **form_data.article}

        updated_article = Article_Table.update_article_by_id(id, updated)
        log.debug(f"Updated Article: {updated_article}")
        if updated_article:
            return ArticleResponse(
                **{
                    **updated_article.model_dump(),
                    "sources": json.loads(
                        updated_article.sources if updated_article.sources else "[]"
                    ),
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ERROR_MESSAGES.DEFAULT(),
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )


@router.put("/{id}/steps", response_model=Optional[ArticleResponse])
async def update_article_steps_by_id(
    id: str, form_data: ArticleStepsForm, user=Depends(get_verified_user)
):
    article = Article_Table.get_article_by_id(id)
    if article:
        updated_article_steps = {
            **article.steps[form_data.step_index],
            **form_data.step,
        }
        article = Article_Table.update_article_steps_by_id(
            id, updated_article_steps, form_data.step_index
        )
        return ArticleResponse(
            **{
                **article.model_dump(),
                "sources": json.loads(article.sources if article.sources else "[]"),
            }
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )


@router.get("/test/view_article_on_series")
async def view_article_on_series():
    article_on_seris = Article_Table.view_article_on_series()
    return article_on_seris


class GenerateArticleForm(BaseModel):
    query: str
    device: str


@router.post("/generate", response_model=Optional[ArticleResponse])
async def generate_new_article(
    form_data: GenerateArticleForm, user=Depends(get_verified_user)
):
    from apps.cisco.article_creator import build_article
    from apps.webui.models.series import Series_Table

    series = Series_Table.get_series_by_name(form_data.device.strip())
    if not series:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.DEFAULT(
                "Series not found. Please contact your admin to create a new series."
            ),
        )
    series_id = series.id

    article = await build_article(form_data.query, form_data.device)

    if article:
        created_article = Article_Table.insert_new_article(
            id=article["id"],
            title=article["title"],
            document_id=article["document_id"],
            objective=article["objective"],
            category=article["category"],
            url=article["url"],
            series_id=series_id,
            introduction=article["introduction"],
            applicable_devices=article["applicable_devices"],
            steps=article["steps"],
            revision_history=article["revision_history"],
            published=False,
            user_id=user.id,
            sources=article.get("sources", None),
        )
        return ArticleResponse(
            **{
                **created_article.model_dump(),
                "sources": json.loads(
                    created_article.sources if created_article.sources else "[]"
                ),
            }
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.DEFAULT(
                "Oops! Something went wrong during article generation."
            ),
        )


@router.delete("/{id}")
async def delete_article_by_id(id: str, user=Depends(get_admin_user)):
    article = Article_Table.get_article_by_id(id)
    if article:
        Article_Table.delete_article_by_id(id)
        return {"message": "Article deleted successfully"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.DEFAULT("Article not found"),
        )


@router.delete("/delete/all")
async def delete_all_articles():
    success = Article_Table.delete_all_articles()
    return {"message": "All articles deleted successfully", "status": success}


@router.get("/editor/review", response_model=List[ArticleModel])
async def get_articles_for_editor_review(user=Depends(get_admin_user)):
    articles = Article_Table.get_articles_for_editor_review()
    return articles


class ReviewArticleForm(BaseModel):
    published: bool


@router.put("/editor/review/{id}", response_model=Optional[ArticleResponse])
async def update_article_review_status_by_id(
    id: str, form_data: ReviewArticleForm, user=Depends(get_admin_user)
):
    article = Article_Table.update_article_review_status_by_id(id, form_data.published)
    if article:
        return ArticleResponse(
            **{
                **article.model_dump(),
                "sources": json.loads(article.sources if article.sources else "[]"),
            }
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.ARTICLE_ATTR_NOT_FOUND("id"),
        )


class UpdateArticlePublishedField(BaseModel):
    published: bool


@router.patch("/update-articles-published", response_model=List[ArticleModel])
async def update_articles(
    form_data: UpdateArticlePublishedField, user=Depends(get_current_user)
):
    print(user)
    articles = Article_Table.get_articles(skip=0, limit=10000)
    updated_articles = []
    for article in articles:
        updated = Article_Table.update_article_by_id(article.id, {"published": True})
        if updated:
            updated_articles.append(updated)

    return updated_articles
