# from langchain.pydantic_v1 import BaseModel, Field
from langchain.schema import Document
from typing import Optional, List, TypedDict, Literal, Any, Dict
from pydantic import BaseModel, Field, ConfigDict, HttpUrl
from sqlalchemy import String, Column, Text, Enum, ForeignKey, BigInteger, Table, text
from sqlalchemy.orm import relationship, Mapped
from enum import Enum as PyEnum
import uuid
import json
import logging
import time
from apps.webui.internal.db import Base, get_db, JSONField
from config import SRC_LOG_LEVELS

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])

####################
# Enum for Categories
####################


class ArticleCategory(str, PyEnum):
    CONFIGURATION = "Configuration"
    MAINTAIN_OPERATE = "Maintain & Operate"
    TROUBLESHOOTING = "Troubleshooting"
    DESIGN = "Design"
    INSTALL_UPGRADE = "Install & Upgrade"


####################
# DB MODEL - Association Table
####################

ARTICLE_ON_SERIES = Table(
    "article_on_series",
    Base.metadata,
    Column("article", ForeignKey("articles.id", ondelete="CASCADE"), primary_key=True),
    Column("series", ForeignKey("series.id", ondelete="CASCADE"), primary_key=True),
)

####################
# DB MODEL - Article
####################


class Article(Base):
    __tablename__ = "articles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    document_id = Column(String, nullable=False, unique=True)
    objective = Column(Text, nullable=True)
    category = Column(Enum(ArticleCategory), nullable=False)
    url = Column(Text, nullable=False)
    applicable_devices = Column(JSONField, nullable=True)
    introduction = Column(Text, nullable=True)
    steps = Column(JSONField, nullable=True)
    revision_history = Column(JSONField, nullable=True)

    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)

    series = relationship(
        "Series",
        secondary=ARTICLE_ON_SERIES,
        back_populates="articles",
    )


####################
# Pydantic Models
####################


class ArticleModel(BaseModel):

    id: str = Field(
        description="The unique identifier for the article.",
    )
    title: str
    document_id: str
    objective: Optional[str] = None
    category: str
    url: Optional[str] = None
    applicable_devices: Optional[List[Any]] = (
        None  # JSON-encoded list of strings (JSONField)
    )
    introduction: Optional[str] = None
    steps: Optional[List[Any]] = None  # JSON-encoded list of dictionaries (JSONField)
    revision_history: Optional[List[Any]] = (
        None  # JSON-encoded list of dictionaries (JSONField)
    )
    created_at: int
    updated_at: int

    series_ids: Optional[List[str]] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True, extra="allow")


class ArticleResponse(BaseModel):
    id: str
    title: str
    document_id: str
    objective: Optional[str]
    category: ArticleCategory
    url: Optional[str]
    applicable_devices: Optional[List[Any]]
    introduction: Optional[str]
    steps: Optional[List[Dict[str, Any]]]
    revision_history: Optional[List[Dict[str, Any]]]
    created_at: int
    updated_at: int


class InsertNewArticleForm(BaseModel):
    title: str
    document_id: str
    objective: Optional[str]
    category: str
    url: str
    applicable_devices: Optional[List[Dict[str, Any]]]
    introduction: Optional[str]
    steps: Optional[List[Dict[str, Any]]]
    revision_history: Optional[List[Dict[str, Any]]]
    series_id: str


class BulkInsertNewArticleForm(BaseModel):
    articles: List[InsertNewArticleForm]


class Search(BaseModel):
    """Search over a database of network switch, router, or wireless access point administration guide or command line guide."""

    query: str = Field(..., description="The original query.")
    subtopics: List[str] = Field(
        ...,
        description="If the original question contains multiple distinct subtopics or if there are more generic subtopics that would be helpful to know in order to answer the original query.",
    )


class Grader(BaseModel):
    """Binary score for grading documents"""

    binary_score: str = Field(
        description="The binary score for grading the relevance of the document. 'yes' if the document is relevant, otherwise 'no'."
    )


class DataSourceType(BaseModel):
    """Represents which contextual documents to load based on the question."""

    datasource: Literal["ADMIN_GUIDE", "CLI_GUIDE"] = Field(
        default="ADMIN_GUIDE",
        description="The resolved type based on the question provided.",
    )


class Step(BaseModel):
    """A single step in the article."""

    section: str = Field(..., description="The heading of the current step number.")
    step_number: int = Field(..., description="The step number of the current section.")
    text: str = Field(
        ..., description="The text/action to be performed in the current step number."
    )
    note: Optional[str] = Field(
        description="Additional notes for the current step or about the current step.",
    )


class Steps(BaseModel):
    """A group of steps within the article."""

    steps: List[Step] = Field(
        description="The steps to guide the user through the configuration."
    )


class CreatedArticle(BaseModel):
    """
    Generate an article from a flow of question(s).
    """

    title: str = Field(
        description="Create a title for the article based on the question and context provided."
    )
    objective: str = Field(
        description="Start with 'The objective of this article is to...' and provide a concise objective in 1-2 sentences."
    )
    introduction: str = Field(
        description="Write a 3-10 sentence introduction explaining the configuration, its features and its importance."
    )
    steps: List[Step] = Field(
        description="The steps to guide the user through the configuration."
    )

    model_config = ConfigDict(from_attributes=True, extra="allow")


class GraphStateKeys(TypedDict, total=False):
    question: str
    documents: List[Document]
    article: Optional[List[CreatedArticle]]
    html: Optional[str]
    datasource: Literal["ADMIN_GUIDE", "CLI_GUIDE"]
    db_articles: Optional[List[Any]]
    db_videos: Optional[List[Any]]
    article_pieces: Optional[Dict[str, Any]]


class GraphState(TypedDict):
    """
    Represents the state of the graph agent in the `ArticleBuilder` flow.
    Attributes:
        keys: A dictionary where each key is a string and the value is expected to be a
              list or another structure that supports addition with 'operator.add'.
    """

    keys: GraphStateKeys


class CreateArticleForm(BaseModel):
    question: str


class ArticlesTable:
    def insert_new_article(
        self,
        *,
        title: str,
        document_id: str,
        objective: str,
        category: ArticleCategory,
        url: str,
        series_id: str,
        introduction: Optional[str] = None,
        applicable_devices: Optional[List[str]] = None,
        steps: Optional[List[Dict[str, Any]]] = None,
        revision_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[ArticleModel]:
        from apps.webui.models.series import Series

        with get_db() as db:
            # Check if the article already exists
            article = db.query(Article).filter_by(document_id=document_id).first()
            if article:
                # Update the article.series if the series is not already associated.
                series = db.query(Series).filter_by(id=series_id).first()
                log.info(f"Series: {series}")
                if series.id not in [series.id for series in article.series]:
                    article.series.append(series)
                    db.commit()
                    db.refresh(article)

                # Create a new article model (this is not inserted into the DB, just returned to the user with updates), attach only the series id to the model
                article_model = ArticleModel(
                    **{
                        "id": article.id,
                        "title": article.title,
                        "document_id": article.document_id,
                        "objective": article.objective,
                        "category": article.category,
                        "url": article.url,
                        "introduction": article.introduction,
                        "applicable_devices": article.applicable_devices,
                        "steps": article.steps,
                        "revision_history": article.revision_history,
                        "series_ids": [series.id for series in article.series],
                        "created_at": article.created_at,
                        "updated_at": article.updated_at,
                    }
                )
                return ArticleModel.model_validate(article_model)
            else:
                # Fetch the series to associate with the article
                series = db.query(Series).filter_by(id=series_id).first()
                if not series:
                    raise ValueError(
                        f"Series with id {series_id} not found. Articles must be associated with a series."
                    )

                # Insert the new article into the database
                result = Article(
                    title=title,
                    document_id=document_id,
                    objective=objective,
                    category=category,
                    url=url,
                    introduction=introduction,
                    applicable_devices=applicable_devices or [],
                    steps=steps or [],
                    revision_history=revision_history or [],
                    created_at=int(time.time()),
                    updated_at=int(time.time()),
                )
                db.add(result)
                db.commit()
                db.refresh(result)

                # Associate the new article with the series
                result.series.append(series)
                db.commit()

                # Return the newly created article
                return ArticleModel.model_validate(result)

    def get_article_by_id(self, id: str) -> Optional[ArticleModel]:
        from apps.webui.models.series import SeriesModel

        try:
            with get_db() as db:
                article = db.query(Article).filter_by(id=id).first()
                series_ids = [series.id for series in article.series]
                article_data = {
                    column.name: getattr(article, column.name)
                    for column in article.__table__.columns
                }
                article_data["series_ids"] = series_ids
                return ArticleModel.model_validate(article_data)
        except Exception as e:
            return None

    def get_article_by_document_id(self, document_id: str) -> Optional[ArticleModel]:
        try:
            with get_db() as db:
                article = db.query(Article).filter_by(document_id=document_id).first()
                return ArticleModel.model_validate(article)
        except Exception as e:
            return None

    def get_article_by_url(self, url: str) -> Optional[ArticleModel]:
        try:
            with get_db() as db:
                article = db.query(Article).filter_by(url=url).first()
                return ArticleModel.model_validate(article)
        except Exception as e:
            return None

    def get_articles(self, skip: int = 0, limit: int = 50) -> List[ArticleModel]:
        from apps.webui.models.series import SeriesModel

        with get_db() as db:
            articles = db.query(Article).offset(skip).limit(limit).all()
            article_models = []
            for article in articles:
                series_ids = [series.id for series in article.series]
                article_data = {
                    column.name: getattr(article, column.name)
                    for column in article.__table__.columns
                }
                article_data["series_ids"] = series_ids
                article_models.append(ArticleModel.model_validate(article_data))
            return article_models

    def get_articles_by_series_id(self, series_id: str) -> List[ArticleModel]:
        with get_db() as db:
            articles = (
                db.query(Article)
                .join(ARTICLE_ON_SERIES, ARTICLE_ON_SERIES.c.article == Article.id)
                .filter(ARTICLE_ON_SERIES.c.series == series_id)
                .all()
            )
            return [ArticleModel.model_validate(article) for article in articles]

    def update_article_by_id(self, id: str, updated: dict) -> Optional[ArticleModel]:
        try:
            with get_db() as db:
                db.query(Article).filter_by(id=id).update(updated)
                db.commit()
                article_obj = db.query(Article).filter_by(id=id).first()
                article_obj.updated_at = int(time.time())
                db.commit()
                db.refresh(article_obj)
                return ArticleModel.model_validate(article_obj)
        except Exception as e:
            return None

    def update_article_steps_by_id(
        self, id: str, updated: dict, step_idx: int
    ) -> Optional[ArticleModel]:
        try:
            with get_db() as db:
                article = db.query(Article).filter_by(id=id).first()
                if article:
                    log.debug(f"Article found: {article.title}")
                    if 0 <= step_idx < len(article.steps):
                        log.debug(f"Updating step {step_idx} for article {id}")
                        steps = list(article.steps)
                        steps[step_idx] = updated
                        article.steps = steps
                        article.updated_at = int(time.time())
                        db.commit()
                        db.refresh(article)
                        return ArticleModel.model_validate(article)
                    else:
                        log.debug(f"Step index {step_idx} out of range")
                        return None
                else:
                    log.debug(f"Article not found: {id}")
                    return None

        except Exception as e:
            return None

    def view_article_on_series(self) -> List[Dict[str, str]]:
        with get_db() as db:
            # Execute the raw SQL query
            result = db.execute(
                text("SELECT article, series FROM article_on_series")
            ).fetchall()

            # Format the results as a list of dictionaries using tuple indices
            article_series_relations = [
                {"article": row[0], "series": row[1]} for row in result
            ]

            return article_series_relations


Article_Table = ArticlesTable()
