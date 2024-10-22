import hashlib
import logging
from typing import Any, Optional, Dict, Union, List, cast
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
import re
import os
import json
import requests
from uuid import uuid4
from lxml import etree
import chromadb.utils.embedding_functions as embedding_functions
from config import BASE_DIR, CHROMA_CLIENT, CollectionFactory
import aiohttp
import asyncio
from chromadb import Documents, EmbeddingFunction, Embeddings
from pydantic import BaseModel


try:
    from bs4 import BeautifulSoup
except ImportError:
    raise ImportError(
        "Webpage requires extra dependencies. Install with `pip install beautifulsoup4==4.12.3`"
    ) from None


class GenerateEmbeddingsForm(BaseModel):
    model: Optional[str] = "llama3.1:latest"
    prompt: str
    options: Optional[dict] = None
    keep_alive: Optional[Union[int, str]] = None


class OllamaEmbeddingFunction(EmbeddingFunction):
    OLLAMA_BASE_URL = "http://localhost:11434"

    def __call__(self, input: Documents) -> Embeddings:
        print("OllamaEmbeddingFunction")
        print(f"Input: {input}")
        # Ensure input is a list of strings
        if not isinstance(input, list) or not all(
            isinstance(doc, str) for doc in input
        ):
            raise ValueError("Input must be a list of strings")

        url = self.OLLAMA_BASE_URL

        try:
            data = GenerateEmbeddingsForm.model_validate({"prompt": input[0]})
            r = requests.request(
                method="POST",
                url=f"{url}/api/embeddings",
                data=data.model_dump_json(exclude_none=True).encode(),
            )
            r.raise_for_status()
            response = r.json()

            if "embedding" in response:
                return response["embedding"]
        except Exception as e:
            logger.exception(e)
            error_detail = "Open WebUI: Server Connection Error"
            if r is not None:
                try:
                    res = r.json()
                    if "error" in res:
                        error_detail = f"Ollama: {res['error']}"
                except:
                    error_detail = f"Ollama: {e}"
            raise ValueError(error_detail)


JSON_DIR = BASE_DIR / "json"

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

openai_embeddings = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.environ.get("OPENAI_API_KEY"), model_name="text-embedding-ada-002"
)
sentence_all_MiniLM_V6_v2_embeddings = embedding_functions.DefaultEmbeddingFunction()

ollama_embeddings = OllamaEmbeddingFunction()


def clean_string(text):
    """
    This function takes in a string and performs a series of text cleaning operations.

    Args:
        text (str): The text to be cleaned. This is expected to be a string.

    Returns:
        cleaned_text (str): The cleaned text after all the cleaning operations
        have been performed.
    """
    # Stripping and reducing multiple spaces to single:
    cleaned_text = re.sub(r"\s+", " ", text.strip())

    # Removing backslashes:
    cleaned_text = cleaned_text.replace("\\", "")

    # Replacing hash characters:
    cleaned_text = cleaned_text.replace("#", " ")

    # Eliminating consecutive non-alphanumeric characters:
    # This regex identifies consecutive non-alphanumeric characters (i.e., not
    # a word character [a-zA-Z0-9_] and not a whitespace) in the string
    # and replaces each group of such characters with a single occurrence of
    # that character.
    # For example, "!!! hello !!!" would become "! hello !".
    cleaned_text = re.sub(r"([^\w\s])\1*", r"\1", cleaned_text)

    return cleaned_text


class WebPageLoader:
    # Shared session for all instances
    _session = requests.Session()

    async def _fetch(
        self, url: str, retries: int = 3, cooldown: int = 2, backoff: float = 1.5
    ) -> str:
        async with aiohttp.ClientSession() as session:
            for i in range(retries):
                try:
                    async with session.get(
                        url,
                        headers=self._session.headers,
                        ssl=None if self._session.verify else False,
                        cookies=self._session.cookies.get_dict(),
                    ) as response:
                        return await response.text()
                except aiohttp.ClientConnectionError as e:
                    if i == retries - 1:
                        raise
                    else:
                        logger.warning(
                            f"Error fetching {url} with attempt "
                            f"{i + 1}/{retries}: {e}. Retrying..."
                        )
                        await asyncio.sleep(cooldown * backoff**i)
        raise ValueError("retry count exceeded")

    async def _fetch_with_rate_limit(
        self, url: str, semaphore: asyncio.Semaphore
    ) -> str:
        async with semaphore:
            try:
                return await self._fetch(url)
            except Exception as e:
                if self.continue_on_failure:
                    logger.warning(
                        f"Error fetching {url}, skipping due to"
                        f" continue_on_failure=True"
                    )
                    return ""
                logger.exception(
                    f"Error fetching {url} and aborting, use continue_on_failure=True "
                    "to continue loading urls after encountering an error."
                )
                raise e

    async def load_data(self, url, **kwargs: Optional[dict[str, Any]]):
        """Load data from a web page using a shared requests' session."""
        all_references = False
        for key, value in kwargs.items():
            if key == "all_references":
                all_references = kwargs["all_references"]

            if key == "requests_per_second" and isinstance(
                kwargs["requests_per_second"], int
            ):
                self.requests_per_second = kwargs["requests_per_second"]
            else:
                self.requests_per_second = 2

        self._session.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*"
            ";q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.google.com/",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        try:
            data = await self._fetch(url)
        except Exception as e:
            logging.error(f"Failed to fetch URL {url}: {e}")
            return {}

        reference_links = self.fetch_reference_links(data)
        if all_references:
            for i in reference_links:
                try:
                    response = await self._fetch(i)
                    data += response
                except Exception as e:
                    logging.error(f"Failed to add URL {url}: {e}")
                    continue

        content = self._get_clean_content(data, url)
        metadata = self._build_metadata(url, data)

        doc_id = hashlib.sha256((content + url).encode()).hexdigest()
        metadata["doc_id"] = doc_id
        return {
            "doc_id": doc_id,
            "data": [{"content": content, "metadata": metadata}],
        }

    @staticmethod
    def _build_metadata(url: str, html: str) -> Dict[str, Union[List[str], str]]:
        metadata = {"url": url}
        concepts = []
        soup = BeautifulSoup(html, "html.parser")
        dom = etree.HTML(str(soup))
        if document_id := soup.find("meta", attrs={"name": "documentId"}):
            metadata["document_id"] = document_id.get(
                "content", hashlib.sha256(uuid4().bytes).hexdigest()
            )
        if title := soup.find("meta", attrs={"name": "description"}):
            metadata["title"] = title.get("content", "Chapter not found.")
        if concept := soup.find("meta", attrs={"name": "concept"}):
            concepts.append(concept.get("content", None))
        if published_date := dom.xpath('//*[@id="documentInfo"]/dl/dd'):
            metadata["published_date"] = published_date[0].text.strip()
        if secondary_concept := soup.find("meta", attrs={"name": "secondaryConcept"}):
            concepts.append(secondary_concept.get("content", None))
        if description := soup.find("meta", attrs={"name": "description"}):
            metadata["description"] = description.get("content", None)

        metadata["concepts"] = ";".join(concepts)
        return metadata

    @staticmethod
    def get_document_id(html: str) -> str:
        soup = BeautifulSoup(html, "html.parser")
        element = soup.find("div", attrs={"class": "documentId"})
        if element:
            pattern = re.compile(r"((?:smb)?\d+)", flags=re.IGNORECASE)
            document_id = pattern.search(element.text.strip())
            return (
                document_id.group(1)
                if document_id
                else hashlib.sha256(uuid4().bytes).hexdigest()
            )
        return hashlib.sha256(uuid4().bytes).hexdigest()

    @staticmethod
    def _get_clean_content(html, url) -> str:
        soup = BeautifulSoup(html, "html.parser")
        original_size = len(str(soup.get_text()))

        tags_to_exclude = [
            "nav",
            "aside",
            "form",
            "header",
            "noscript",
            "svg",
            "canvas",
            "footer",
            "script",
            "style",
        ]
        for tag in soup(tags_to_exclude):
            tag.decompose()

        ids_to_exclude = [
            "sidebar",
            "main-navigation",
            "menu-main-menu",
            "fw-skiplinks",
            "download-list-container",
            "skiplink-content",
            "skiplink-search",
            "skiplink-footer",
        ]
        for id_ in ids_to_exclude:
            tags = soup.find_all(id=id_)
            for tag in tags:
                tag.decompose()

        classes_to_exclude = [
            "elementor-location-header",
            "navbar-header",
            "nav",
            "header-sidebar-wrapper",
            "blog-sidebar-wrapper",
            "related-posts",
            "narrow-v2",
            "linksRow",
            "docHeaderComponent",
            "availableLanguagesList",
            "disclaimers",
        ]
        for class_name in classes_to_exclude:
            tags = soup.find_all(class_=class_name)
            for tag in tags:
                tag.decompose()

        content = soup.get_text()
        content = clean_string(content)

        cleaned_size = len(content)
        if original_size != 0:
            logger.info(
                f"[{url}] Cleaned page size: {cleaned_size} characters, down from {original_size} (shrunk: {original_size-cleaned_size} chars, {round((1-(cleaned_size/original_size)) * 100, 2)}%)"  # noqa:E501
            )

        return content

    @classmethod
    def close_session(cls):
        cls._session.close()

    def fetch_reference_links(self, data):
        soup = BeautifulSoup(data, "html.parser")
        a_tags = soup.find_all("a", href=True)
        reference_links = [a["href"] for a in a_tags if a["href"].startswith("http")]
        return reference_links


loader = WebPageLoader()


def convert_to_lc_document(article: dict[str, any]) -> Document:
    metadata = article["data"]["metadata"]
    metadata["id"] = article["doc_id"]
    return Document(page_content=article["data"]["content"], metadata=metadata)


def insert_article_into_vectordb(article: dict[str, any], collections: str):
    """
    This function inserts an article into the VectorDB database.

    Args:
        article (dict): The article to be inserted into the database.
        collection_name (str): The name of the collection in which the article
        is to be inserted.
    """

    collection = CHROMA_CLIENT.get_or_create_collection(name=collections)
    ids = [article["doc_id"]]
    content = [article["data"][0]["content"]]
    metadatas = [article["data"][0]["metadata"]]

    if len(ids) == len(metadatas):
        for i, metadata in enumerate(metadatas):
            metadata["doc_id"] = ids[i]

    if len(content[0]) > 8192:
        return False

    try:
        collection.add(ids=ids, documents=content, metadatas=metadatas)
        return True
    except ValueError as err:
        logger.error(f"Error adding document to collection: {err}")
        return False


def save_article_content_to_json(data: list[dict[str, any]]):
    with open(JSON_DIR / "articles_content.json", "w") as f:
        json.dump(data, f)


def get_articles_from_json():
    try:
        with open(JSON_DIR / "articles_content.json") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def iterate_json_articles(articles: list[dict[str, any]]):
    for article in articles:
        try:
            inserted = insert_article_into_vectordb(
                article, article["data"][0]["metadata"]["collection"]
            )
        except ValueError as err:
            logger.error(f"Error inserting article: {err}")
            continue
        print(f"Inserted: {inserted}")


def scrape_articles(articles: list[dict[str, any]] = []):
    documents = []
    for article in articles:
        url = article["url"]
        series = article["series"]
        collection_name = CollectionFactory.get_article_collection(series)
        logger.info(f"Scraping article: {url}")
        if not collection_name:
            continue
        document = asyncio.run(loader.load_data(url))
        document["data"][0]["metadata"]["collection"] = collection_name
        documents.append(document)

    save_article_content_to_json(documents)

    for document in documents:
        collection_name: str = document["data"][0]["metadata"]["collection"]
        try:
            inserted = insert_article_into_vectordb(document, collection_name)
        except ValueError as err:
            logger.error(f"Error inserting article: {err}")
            continue
        print(f"Inserted: {inserted}")


def query_vectordb():
    articles = json.loads(open(JSON_DIR / "articles.json").read())

    for article in articles:
        pass


def seed_articles_to_vectordb():
    articles = get_articles_from_json()
    print(articles)
    if not articles or len(articles) == 0:
        articles = json.loads(open(JSON_DIR / "articles.json").read())
        scrape_articles(articles)
    else:
        iterate_json_articles(articles)


def peek_db_collections():
    collections = CHROMA_CLIENT.list_collections()
    for collection in collections:
        print(collection)


def reset_db():
    reset = CHROMA_CLIENT.reset()
    print(reset)


if __name__ == "__main__":
    seed_articles_to_vectordb()
    # peek_db_collections()
    # reset_db()
