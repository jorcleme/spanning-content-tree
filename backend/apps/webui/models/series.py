from langchain.schema import Document
from typing import Optional, List, TypedDict, Literal, Any, Dict
from pydantic import BaseModel, Field, ConfigDict, field_serializer
from sqlalchemy import String, Column, Text, Enum, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
import uuid
import logging
import time
from apps.webui.internal.db import Base, get_db, JSONField
from config import SRC_LOG_LEVELS
from apps.webui.models.articles import ArticleModel, ARTICLE_ON_SERIES

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])

####################
# DB MODEL - Series
####################


class Series(Base):
    __tablename__ = "series"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True)
    admin_guide_urls = Column(JSONField, nullable=True)
    datasheet_urls = Column(JSONField, nullable=True)
    cli_guide_urls = Column(JSONField, nullable=True)
    software_url = Column(Text, nullable=True)

    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)

    # Many-to-Many relationship with Articles
    articles = relationship(
        "Article", secondary=ARTICLE_ON_SERIES, back_populates="series"
    )


####################
# Pydantic Models
####################


class SeriesModel(BaseModel):
    id: str
    name: str
    admin_guide_urls: List[Any]
    datasheet_urls: List[Any]
    cli_guide_urls: Optional[List[Any]]
    software_url: Optional[str]

    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)


class InsertNewSeriesForm(BaseModel):
    name: str
    admin_guide_urls: Optional[List[str]]
    datasheet_urls: Optional[List[str]]
    cli_guide_urls: Optional[List[str]]
    software_url: Optional[str]


class SeriesTable:
    def insert_new_series(
        self,
        name: str,
        admin_guide_urls: List[str],
        datasheet_urls: List[str],
        cli_guide_urls: List[str],
        software_url: str,
    ) -> Optional[SeriesModel]:
        with get_db() as db:
            result = Series(
                name=name,
                admin_guide_urls=admin_guide_urls,
                datasheet_urls=datasheet_urls,
                cli_guide_urls=cli_guide_urls,
                software_url=software_url,
                created_at=int(time.time()),
                updated_at=int(time.time()),
            )
            db.add(result)
            db.commit()
            db.refresh(result)
            if result:
                return SeriesModel.model_validate(result)
            else:
                return None

    def get_series_by_id(self, id: str) -> Optional[SeriesModel]:
        try:
            with get_db() as db:
                series = db.query(Series).filter_by(id=id).first()
                return SeriesModel.model_validate(series, from_attributes=True)
        except Exception as e:
            log.error(f"Error getting series by id: {e}")
            return None

    def get_series_by_name(self, name: str) -> Optional[SeriesModel]:
        try:
            with get_db() as db:
                series = db.query(Series).filter_by(name=name).first()
                return SeriesModel.model_validate(series)
        except Exception as e:
            log.error(f"Error getting series by name: {e}")
            return None

    def get_all_series(self, skip: int = 0, limit: int = 50) -> List[SeriesModel]:
        try:
            with get_db() as db:
                series = db.query(Series).offset(skip).limit(limit).all()
                return [SeriesModel.model_validate(s) for s in series]
        except Exception as e:
            log.error(f"Error getting all series: {e}")
            return []

    def get_series_with_articles(self, series_id: str) -> Optional[SeriesModel]:
        try:
            with get_db() as db:
                series = db.query(Series).filter_by(id=series_id).first()
                if series:
                    articles = series.articles
                    series.articles = [ArticleModel.model_validate(a) for a in articles]
                    return SeriesModel.model_validate(series)
                else:
                    return None
        except Exception as e:
            log.error(f"Error getting series with articles: {e}")
            return None

    def delete_all_series(self) -> bool:
        try:
            with get_db() as db:
                db.query(Series).delete()
                db.commit()
                return True
        except Exception as e:
            log.error(f"Error deleting all series: {e}")
            return False


Series_Table = SeriesTable()
