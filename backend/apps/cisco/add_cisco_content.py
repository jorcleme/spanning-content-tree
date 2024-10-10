import json
from config import DATA_DIR
import requests
import argparse
import logging
import sys
import urllib.parse

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


WEBUI_API_URL = "http://localhost:8080/api/v1"
ARTICLES_API_URL = f"{WEBUI_API_URL}/articles"
SERIES_API_URL = f"{WEBUI_API_URL}/series"

SCHEMA_DIR = f"{DATA_DIR}/cisco/schema"


def insert_series():
    series_data = json.loads(open(f"{SCHEMA_DIR}/series.json", encoding="utf-8").read())

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


def update_articles_for_series():
    try:
        articles = json.loads(
            open(f"{SCHEMA_DIR}/articles.json", encoding="utf-8").read()
        )
    except Exception as e:
        logger.error(f"Error reading articles.json: {e}")
        return

    for article in articles:

        try:
            series_name = article.get("series", None)
            if not series_name:
                logger.warning("Series name is missing in article, skipping.")
                continue

            db_articles = requests.post(
                f"{ARTICLES_API_URL}/url", json={"url": article.get("url")}
            )
            db_articles.raise_for_status()
            db_article = db_articles.json()

            article_schema = {
                "id": db_article.get("id"),
                "title": db_article.get("title"),
                "document_id": db_article.get("document_id"),
                "url": db_article.get("url"),
                "category": db_article.get("category"),
                "objective": db_article.get("objective"),
                "introduction": db_article.get("introduction"),
                "applicable_devices": db_article.get("applicable_devices", []),
                "steps": db_article.get("steps", []),
            }
            for step in article_schema["steps"]:
                if "qa_pairs" in step:
                    del step["qa_pairs"]

            article_schema["steps"] = list(
                map(
                    lambda x: {
                        **x,
                        **{
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
                            ]
                        },
                    },
                    article_schema["steps"],
                )
            )

            update_res = requests.put(
                f"{ARTICLES_API_URL}/{db_article.get('id')}",
                json={"article": article_schema},
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjVlMjhjODQ5LTU0NjUtNDE1Yi1hZWE2LTQ3NGRmOTJlODcwNiJ9.a1FuXpo55HXltYGB-Vnrxw-_WhepMwlIKua1uBF-rtY",
                },
            )
            update_res.raise_for_status()
            updated_article = update_res.json()
            logger.info(f"Updated article: {json.dumps(updated_article, indent=2)}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for article {article.get('url')}: {e}")
        except Exception as e:
            logger.error(f"Error processing article {article.get('url')}: {e}")


# If you want to manually insert articles, you can use the following function
# Use Postman to retrieve the Series ID for each series and update the series_to_ids dictionary
def insert_articles_for_series():
    articles_data = json.loads(
        open(f"{SCHEMA_DIR}/articles.json", encoding="utf-8").read()
    )

    for article in articles_data:
        series_name = article.get("series", None)
        series_to_ids = {
            "Cisco Business 220 Series Smart Switches": "cec1a92b-aab4-44b3-9c9d-520e2d2f8b56",
            "Cisco Business 250 Series Smart Switches": "3b16b345-7307-4715-a350-90ab1e87f03b",
            "Cisco Business 350 Series Managed Switches": "2a331d05-fdaa-4b7b-bbdc-c77ab34721db",
            "Cisco Catalyst 1200 Series Switches": "6462c4eb-0d6c-4ffb-b650-b3ef9c37842f",
            "Cisco Catalyst 1300 Series Switches": "9cbd4de5-1540-44e7-b4b4-e3f06fe9cc6e",
            "Cisco 350 Series Managed Switches": "c4aa811a-e31b-4482-9e31-8390c815ad8f",
            "Cisco 350X Series Stackable Managed Switches": "0d0461c3-9c66-4b6e-8030-16528c0bd0ec",
            "Cisco 550X Series Stackable Managed Switches": "50015e9c-5f31-42b8-bde7-fac00cbb1c38",
            "RV100 Product Family": "f2a66418-1f5e-402f-a7cb-4476b5d70c95",
            "RV320 Product Family": "34001555-7a0d-44a0-9b79-baabe28fa1ca",
            "RV340 Product Family": "235e839b-4f8e-4e69-9f85-0e9fe50d24ac",
            "RV160 VPN Router": "9af14190-bd7a-4e11-b125-27228620bc0a",
            "RV260 VPN Router": "602d3130-66b7-4e86-8134-d37e3b54e253",
            "Cisco Business Wireless AC": "ae297020-4e7f-4eb1-936c-4dc436d9172d",
            "Cisco Business Wireless AX": "c3c1f033-ab5e-4bc2-90a6-73ace9f9a012",
        }

        try:
            series_res = requests.get(
                f"{SERIES_API_URL}/name/{urllib.parse.quote(series_name, safe='/:?=&')}"
            )
            print(f"Request to fetch series returned status: {series_res.status_code}")
            series_res.raise_for_status()  # Raise an exception for bad responses
            data = series_res.json()
            print(f"Series data: {json.dumps(data, indent=2)}")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching series data: {e}")
            continue

        series_id = series_to_ids.get(series_name, None)
        if series_id:
            print(f"Series ID for {series_name}: {series_id}")
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

            # Log the payload for inspection
            print(f"Article payload: {json.dumps(article_schema, indent=2)}")

            # Post the new article
            try:
                res = requests.post(f"{ARTICLES_API_URL}/add", json=article_schema)
                print(f"Article POST returned status: {res.status_code}")
                res.raise_for_status()  # Raise an exception for bad responses

                # Check if the response is valid JSON
                try:
                    data = res.json()
                    print(f"JSON Response: {json.dumps(data, indent=2)}")
                except requests.exceptions.JSONDecodeError:
                    print("The response is not valid JSON")
            except requests.exceptions.RequestException as e:
                print(f"Error posting article: {e}")


def add_article(article: dict):
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


def seed():
    insert_series()
    series = get_all_series()
    articles = json.loads(open(f"{SCHEMA_DIR}/articles.json", encoding="utf-8").read())

    for article in articles:
        series_name = article.get("series", None)
        series_id = None
        for s in series:
            if s.get("name") == series_name:
                series_id = s.get("id")
                break
        if series_id:
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
            }
            is_article_added = add_article(article_schema)
            if is_article_added:
                logger.info(f"Article added: {article.get('title')}")
            else:
                logger.error(f"Error adding article: {article.get('title')}")


def get_all_series():
    res = requests.get(f"{SERIES_API_URL}")
    res.raise_for_status()
    try:
        data = res.json()
        print(f"JSON Response: {json.dumps(data, indent=2)}")
    except requests.exceptions.JSONDecodeError:
        print("The response is not valid JSON")

    return data


if __name__ == "__main__":
    update_articles_for_series()
    # insert_articles_for_series()
    # parser = argparse.ArgumentParser(description="Seed Cisco content")
    # parser.add_argument("--f", type=str, required=False, help="Function to run")

    # args = parser.parse_args()

    # function_mapping = {
    #     "insert_series": insert_series,
    #     "insert_articles_for_series": insert_articles_for_series,
    #     "seed": seed,
    # }

    # function_to_run = function_mapping.get(args.f, None)
    # if function_to_run:
    #     function_to_run()
    # else:
    #     logger.error(
    #         f"Function '{args.f}' not found. Available functions: {list(function_mapping.keys())}"
    #     )
    #     sys.exit(1)
