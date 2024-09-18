import json
from config import DATA_DIR
import requests
import aiohttp
import asyncio
import logging
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

        series_schema = {
            "name": series.get("family", None),
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

        res = requests.post(f"{SERIES_API_URL}/add", json=series_schema)
        print(f"Status Code: {res.status_code}")
        print(f"Response Text: {res.text}")

        try:
            data = res.json()
            print(f"JSON Response: {data}")
        except requests.exceptions.JSONDecodeError:
            print("The response is not valid JSON")


def insert_articles_for_cbs220():
    articles_data = json.loads(
        open(f"{SCHEMA_DIR}/articles.json", encoding="utf-8").read()
    )

    for article in articles_data:
        series_name = article.get("series", None)

        # Only focus on Cisco Business 220 Series Smart Switches
        if series_name and series_name == "RV320 Product Family":
            print(f"Found article for series: {series_name}")

            # Make the request to fetch the series details
            try:
                series_res = requests.get(
                    f"{SERIES_API_URL}/name/{urllib.parse.quote(series_name, safe='/:?=&')}"
                )
                print(
                    f"Request to fetch series returned status: {series_res.status_code}"
                )
                series_res.raise_for_status()  # Raise an exception for bad responses
                data = series_res.json()
            except requests.exceptions.RequestException as e:
                print(f"Error fetching series data: {e}")
                continue

            series_id = "09fde4a8-24eb-48fb-a1b9-87889d1eb046"
            if not series_id:
                print(f"No series ID found for series name: {series_name}")
                continue

            print(f"Series ID for {series_name}: {series_id}")

            # Construct the article payload
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

            # Log the payload for inspection
            print(f"Article payload: {json.dumps(article_schema, indent=2)}")

            # Post the new article
            try:
                res = requests.post(f"{ARTICLES_API_URL}/add", json=article_schema)
                print(f"Article POST returned status: {res.status_code}")
                res.raise_for_status()  # Raise an exception for bad responses
                print(f"Response Text: {res.text}")

                # Check if the response is valid JSON
                try:
                    data = res.json()
                    print(f"JSON Response: {json.dumps(data, indent=2)}")
                except requests.exceptions.JSONDecodeError:
                    print("The response is not valid JSON")
            except requests.exceptions.RequestException as e:
                print(f"Error posting article: {e}")


class HttpFetcher:

    def __init__(
        self,
        requests_per_second: int = 2,
        continue_on_failure: bool = True,
        ssl_verify: bool = False,
    ):
        self._session = requests.Session()
        default_header_template = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
            "Accept": "application/json,text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*"
            ";q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.google.com/",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        self._session.headers.update(default_header_template)
        self.requests_per_second = requests_per_second
        self.continue_on_failure = continue_on_failure
        self.ssl_verify = ssl_verify
        if not self.ssl_verify:
            self._session.verify = False

    async def _post(
        self,
        url: str,
        data: dict,
        retries: int = 3,
        cooldown: int = 2,
        backoff: float = 1.5,
    ):
        async with aiohttp.ClientSession() as session:
            for i in range(retries):
                try:
                    async with session.post(
                        url,
                        headers=self._session.headers,
                        ssl=None if self._session.verify else False,
                        cookies=self._session.cookies,
                        data=data,
                    ) as response:
                        return await response.json()
                except aiohttp.ClientError as e:
                    if i == retries - 1:
                        raise e
                    else:
                        logger.warning(
                            f"Error posting to {url} with attempt {i + 1}/{retries}: {e}. Retrying in {cooldown} seconds."
                        )
                        await asyncio.sleep(cooldown * backoff**i)

    async def _post_with_rate_limit(
        self, url: str, data: dict, semaphore: asyncio.Semaphore
    ) -> str:
        async with semaphore:
            try:
                return await self._post(url, data)
            except Exception as e:
                if self.continue_on_failure:
                    logger.warning(
                        f"Error post {url}, skipping due to"
                        f" continue_on_failure=True"
                    )
                    return ""
                logger.exception(
                    f"Error fetching {url} and aborting, use continue_on_failure=True "
                    "to continue loading urls after encountering an error."
                )
                raise e

    async def post_all(self, urls: list[str], data: dict) -> any:
        semaphore = asyncio.Semaphore(self.requests_per_second)
        tasks = []
        for url in urls:
            task = asyncio.ensure_future(
                self._post_with_rate_limit(url, data, semaphore)
            )
            tasks.append(task)

        try:
            from tqdm.asyncio import tqdm_asyncio

            return await tqdm_asyncio.gather(
                *tasks, desc="Posting data to URLs", ascii=True, mininterval=1
            )

        except ImportError:
            logger.warning("tqdm not installed, skipping progress bar")
            return await asyncio.gather(*tasks)

    async def post(self, url: str, data: dict) -> any:
        return await self._post(url, data)


async def ainsert_articles():
    articles_data = json.loads(
        open(f"{SCHEMA_DIR}/articles.json", encoding="utf-8").read()
    )

    fetcher = HttpFetcher(
        requests_per_second=2, continue_on_failure=True, ssl_verify=False
    )
    tasks = []
    for article in articles_data:
        series_name = article.get("series", None)

        if series_name:
            print(f"Series Name: {series_name}")
            article_schema = {
                "series_name": series_name,
                "title": article.get("title"),
                "document_id": article.get("document_id"),
                "url": article.get("url"),
                "category": article.get("category"),
                "objective": article.get("objective"),
                "introduction": article.get("introduction"),
                "applicable_devices": article.get("applicable_devices", []),
                "steps": article.get("steps", []),
            }

            tasks.append(fetcher.post(f"{ARTICLES_API_URL}/add", data=article_schema))

    responses = await asyncio.gather(*tasks)

    for res in responses:
        print(f"Response: {res}")


def insert_articles():
    articles_data = json.loads(
        open(f"{SCHEMA_DIR}/articles.json", encoding="utf-8").read()
    )

    for article in articles_data:

        series_name = article.get("series", None)

        if series_name:
            print(f"Series Name: {series_name}")
            article_schema = {
                "series_name": series_name,
                "title": article.get("title"),
                "document_id": article.get("document_id"),
                "url": article.get("url"),
                "category": article.get("category"),
                "objective": article.get("objective"),
                "introduction": article.get("introduction"),
                "applicable_devices": article.get("applicable_devices", []),
                "steps": article.get("steps", []),
            }

            res = requests.post(f"{ARTICLES_API_URL}/add", json=article_schema)
            print(f"Status Code: {res.status_code}")
            print(f"Response Text: {res.text}")

            try:
                data = res.json()
                print(f"JSON Response: {data}")
            except requests.exceptions.JSONDecodeError:
                print("The response is not valid JSON")


if __name__ == "__main__":
    insert_articles_for_cbs220()
