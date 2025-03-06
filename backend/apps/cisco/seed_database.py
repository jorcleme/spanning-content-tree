"""
This script seeds the Cisco Product Families and Articles into the database.

Prerequisites:
    1. Ensure you have activated the virtual environment.
        $ cd backend
        $ source env/bin/activate (Linux/Mac)
        $ .\env\Scripts\activate (Windows)
       
    2. Start the backend server.
        $ cd backend (if not already in the backend directory)
        $ bash start.sh (Linux/Mac)
        $ .\start.bat (Windows)
        

Notes:
    1. Starting the backend server runs migrations automatically.
    2. This script utilizes API endpoints to insert data so its paramount that the backend server is running.
    3. As of now, anybody can use the API endpoint to upload Series/Articles. This will be restricted in the future. e.g., depends(is_admin_user)

Usage:
    1. To run the script as a module (from the backend directory):
        $ python -m apps.cisco.seed_database

Functions:
    - insert_series: Inserts series data into the database.
    - insert_articles_for_series: Inserts articles data into the database. Note: insert_series should be run before this function.
    - seed: Runs both insert_series and insert_articles_for_series sequentially.

Arguments:
    --f: Specifies which function to run. Available functions: insert_series, insert_articles_for_series, seed. Default: seed (runs all functions).
"""

import json
import os
import time
from config import BASE_DIR
import requests
import argparse
import logging
import sys
import asyncio
import urllib.parse
from typing import TypedDict, List, Any, Dict, Optional


class SeriesSchema(TypedDict, total=False):
    id: str
    name: str
    admin_guide_urls: List[str]
    datasheet_urls: List[str]
    cli_guide_urls: List[str]
    software_url: str
    created_at: int
    updated_at: int


class ArticlesSchema(TypedDict, total=False):
    id: str
    title: str
    document_id: str
    objective: str
    category: str
    url: str
    applicable_devices: List[Dict[str, Any]]
    introduction: Optional[str]
    steps: List[Dict[str, Any]]
    revision_history: Optional[List[Dict[str, Any]]]
    published: bool
    user_id: Optional[str]
    sources: Optional[List[str]]
    created_at: int
    updated_at: int
    series_ids: List[str]


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

WEBUI_API_URL = "http://localhost:8080/api/v1"
ARTICLES_API_URL = f"{WEBUI_API_URL}/articles"
SERIES_API_URL = f"{WEBUI_API_URL}/series"
JSON_DIR = f"{BASE_DIR}/json"


async def insert_series():
    series_data = json.loads(open(f"{JSON_DIR}/series.json", encoding="utf-8").read())

    for series in series_data:
        series_name = series.get("family", None)
        if not series_name:
            logger.warning(
                f"Series name not found for series: {series}. Skipping entry..."
            )
            continue

        try:
            check_res = requests.get(
                f"{SERIES_API_URL}/name/{urllib.parse.quote(series_name, safe='/:?=&')}"
            )
            if check_res.status_code == 200:
                logger.info(
                    f"Series '{series_name}' already exists. Skipping insertion..."
                )
                continue
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching series data: {e}")
            continue

        series_schema = {
            "name": series_name,
            "admin_guide_urls": (
                [series.get("admin_guide_url")] if series.get("admin_guide_url") else []
            ),
            "datasheet_urls": (
                series.get("datasheet_url", [])
                if isinstance(series.get("datasheet_url"), list)
                else (
                    [series.get("datasheet_url")] if series.get("datasheet_url") else []
                )
            ),
            "cli_guide_urls": [],
            "software_url": series.get("software_url", None),
        }

        try:
            res = requests.post(f"{SERIES_API_URL}/add", json=series_schema)
            logger.info(f"Status Code: {res.status_code}")
            res.raise_for_status()
            try:
                data = res.json()
                logger.info(f"JSON Response: {json.dumps(data, indent=2)}")
            except requests.exceptions.JSONDecodeError:
                logger.error("The response is not valid JSON")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error posting series: {e}")


async def get_all_series():
    try:
        res = requests.get(f"{SERIES_API_URL}")
        print(f"Request to fetch all series returned status: {res.status_code}")
        res.raise_for_status()  # Raise an exception for bad responses
        series: List[SeriesSchema] = res.json()
        print(f"Series JSON Response: {json.dumps(series, indent=2)}")
        return series
    except requests.exceptions.RequestException as e:
        print(f"Error fetching series data: {e}")
        return None


# If you want to manually insert articles, you can use the following function
# Note: The `insert_series` function should be run before this function
async def insert_articles_for_series():
    series = await get_all_series()
    if not series or (isinstance(series, list) and len(series) == 0):
        logger.error(
            "The database contains no series (Product Families). Running insert_series()..."
        )
        await insert_series()
        series = await get_all_series()

    series_map: dict[str, str] = {s["name"]: s["id"] for s in series}
    articles_data = json.loads(
        open(f"{JSON_DIR}/articles.json", encoding="utf-8").read()
    )

    for article in articles_data:
        series_name = article.get("series", None)
        if not series_name:
            logger.info(
                "Series name is missing in article. An article must be associated with a series or many series. Skipping...."
            )
            continue
        series_id = series_map.get(series_name, None)
        if series_id:
            try:
                article_schema = {
                    "series_id": series_id,
                    "title": article.get("title"),
                    "document_id": article.get("document_id"),
                    "url": article.get("url"),
                    "category": article.get("category"),
                    "objective": article.get("objective"),
                    "introduction": article.get("introduction"),
                    "applicable_devices": article.get("applicable_devices", []),
                    "steps": article.get("steps", []),
                    "revision_history": article.get("revision_history", []),
                    "published": True,
                }
                article_schema["steps"] = list(
                    map(
                        lambda x: {
                            **x,
                            "qna_pairs": [
                                {
                                    "id": "static_1",
                                    "question": "I don't understand this step",
                                    "answer": None,
                                },
                                {
                                    "id": "static_2",
                                    "question": "I need help troubleshooting",
                                    "answer": None,
                                },
                                {
                                    "id": "static_3",
                                    "question": "Show best practices",
                                    "answer": None,
                                },
                            ],
                        },
                        article_schema["steps"],
                    )
                )

                res = requests.post(f"{ARTICLES_API_URL}/add", json=article_schema)
                print(f"Article POST returned status: {res.status_code}")
                res.raise_for_status()  # Raise an exception for bad responses
                article = res.json()
                print(f"Article JSON Response: {json.dumps(article, indent=2)}")

            except Exception as e:
                print(f"Error processing article: {e}")
                continue


async def add_article(article: dict):
    try:
        res = requests.post(f"{ARTICLES_API_URL}/add", json=article)
        logger.info(f"Article POST returned status: {res.status_code}")
        res.raise_for_status()  # Raise an exception for bad responses
        data = res.json()
        logger.info(f"JSON Response: {json.dumps(data, indent=2)}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Error posting article: {e}")
        return False


async def seed():
    await insert_series()
    await insert_articles_for_series()


if __name__ == "__main__":
    functions = {
        "insert_series": insert_series,
        "insert_articles_for_series": insert_articles_for_series,
        "seed": seed,
    }
    parser = argparse.ArgumentParser(
        description="Seed Cisco Product Families and Articles"
    )
    parser.add_argument(
        "--f",
        type=str,
        required=False,
        help=f"Which function to run. Available functions: {list(functions.keys())}. Default: seed (runs all functions)",
        default="seed",
    )

    args = parser.parse_args()

    func = functions.get(args.f, seed)
    asyncio.run(func())
