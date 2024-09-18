import logging

from fastapi import Depends, HTTPException, status
from fastapi.responses import Response

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

from apps.webui.models.series import Series_Table, SeriesModel, InsertNewSeriesForm
from constants import ERROR_MESSAGES
from config import SRC_LOG_LEVELS

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])

router = APIRouter()


################
# GetSeries
################


@router.get("/", response_model=List[SeriesModel])
async def get_series(skip: int = 0, limit: int = 50):
    series = Series_Table.get_all_series(skip=skip, limit=limit)
    return series


################
# GetSeriesById
################


@router.get("/{id}", response_model=Optional[SeriesModel])
async def get_series_by_id(id: str):
    series = Series_Table.get_series_by_id(id)

    if series:
        return series
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.SERIES_NOT_FOUND,
        )


##################
# GetSeriesByName
##################


@router.get("/name/{name}", response_model=Optional[SeriesModel])
async def get_series_by_name(name: str):
    series = Series_Table.get_series_by_name(name)

    if series:
        return series
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.SERIES_NOT_FOUND,
        )


################
# GetSeriesArticles
################


@router.get("/{id}/articles", response_model=Optional[SeriesModel])
async def get_series_with_articles(id: str):
    series = Series_Table.get_series_with_articles(series_id=id)

    if series:
        return series
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ERROR_MESSAGES.SERIES_NOT_FOUND,
        )


################
# AddNewSeries
################


@router.post("/add", response_model=Optional[SeriesModel])
async def insert_new_series(form_data: InsertNewSeriesForm):
    series = Series_Table.insert_new_series(
        name=form_data.name,
        admin_guide_urls=form_data.admin_guide_urls,
        datasheet_urls=form_data.datasheet_urls,
        cli_guide_urls=form_data.cli_guide_urls,
        software_url=form_data.software_url,
    )
    if series:
        return series
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.DEFAULT(),
        )
