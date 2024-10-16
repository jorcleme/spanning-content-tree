import json
import requests
import re
import uuid
import logging
from pathlib import Path
from bs4 import BeautifulSoup, Tag
from lxml import etree
from typing import (
    List,
    Iterator,
    Dict,
    Any,
    Union,
    Optional,
    Literal,
    Tuple,
    Type,
    Callable,
)
from langchain_text_splitters import TextSplitter
from langchain_core.documents import Document
from langchain_core.document_loaders import BaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from transformers import GPT2Tokenizer
from config import (
    CHROMA_CLIENT,
    CATALYST_1200_ADMIN_GUIDE_COLLECTION,
    CATALYST_1200_CLI_GUIDE_COLLECTION,
    CATALYST_1300_ADMIN_GUIDE_COLLECTION,
    CATALYST_1300_CLI_GUIDE_COLLECTION,
    CBS_220_ADMIN_GUIDE_COLLECTION,
    CBS_220_CLI_GUIDE_COLLECTION,
    CBS_250_ADMIN_GUIDE_COLLECTION,
    CBS_250_CLI_GUIDE_COLLECTION,
    CBS_350_ADMIN_GUIDE_COLLECTION,
    CBS_350_CLI_GUIDE_COLLECTION,
    CISCO_350_ADMIN_GUIDE_COLLECTION,
    CISCO_350_CLI_GUIDE_COLLECTION_NAME,
    CISCO_350X_ADMIN_GUIDE_COLLECTION_NAME,
    CISCO_350X_CLI_GUIDE_COLLECTION_NAME,
    CISCO_550X_ADMIN_GUIDE_COLLECTION_NAME,
    CISCO_550X_CLI_GUIDE_COLLECTION_NAME,
    BASE_DIR,
    CollectionFactory,
)
from collections.abc import Callable
import chromadb.utils.embedding_functions as embedding_functions
import os
from dotenv import load_dotenv
from utils.vector_dimensions import Providers, EmbeddingFunctions, VectorDimensions

try:
    from chromadb.api.types import EmbeddingFunction, Embeddings
except RuntimeError:
    from utils.misc import use_pysqlite3

    use_pysqlite3()
    from chromadb.api.types import EmbeddingFunction, Embeddings


class EmbeddingFunc(EmbeddingFunction):
    def __init__(self, embedding_fn: Callable[[list[str]], list[str]]):
        self.embedding_fn = embedding_fn

    def __call__(self, input: Any) -> Embeddings:
        return self.embedding_fn(input)


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

SourceMap = Dict[str, Dict[str, Tuple[str, str]]]
MAX_TOKENS = 8192

openai_embeddings = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.environ.get("OPENAI_API_KEY"), model_name="text-embedding-ada-002"
)
sentence_all_MiniLM_V6_v2_embeddings = embedding_functions.DefaultEmbeddingFunction()


class CLIParser:
    DESCRIPTION = "description"
    COMMAND_NAME = "command_name"
    TOPIC = "topic"
    SYNTAX = "syntax"
    PARAMETERS = "parameters"
    DEFAULT_CONFIGURATION = "default_configuration"
    COMMAND_MODE = "command_mode"
    USER_GUIDELINES = "user_guidelines"
    EXAMPLES = "examples"

    def __init__(self):
        pass

    @staticmethod
    def sanitize_text(text: str) -> str:
        cleaned_text = re.sub(r"\s+", " ", text.strip())
        cleaned_text = cleaned_text.replace("\\", "")
        cleaned_text = cleaned_text.replace("#", " ")
        cleaned_text = re.sub(r"([^\w\s])\1*", r"\1", cleaned_text)
        return cleaned_text

    def load(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        return self._parse(soup)

    def _parse(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        cli_sections = []
        page_article_bodies = soup.find_all(
            "article", class_=("topic", "reference", "nested1")
        )
        if not page_article_bodies or len(page_article_bodies) == 0:
            print(
                "No article body found. This is usually an index page or reference page."
            )
            return cli_sections

        for article_body in page_article_bodies:
            topic_sections = article_body.find_all("section", class_=("body"))
            topic = soup.find("meta", attrs={"name": "description"}).get(
                "content", None
            )
            for section in topic_sections:
                if re.match(
                    r"^This chapter contains the following sections:",
                    section.get_text().strip(),
                ):
                    continue
                command_name = section.find_previous(class_=("title",)).get_text(
                    strip=True
                )
                if topic and topic == "Introduction":
                    cli_sections.append(
                        self._parse_intro_section(section, command_name, topic)
                    )
                else:
                    cli_sections.append(
                        self._parse_detail_section(section, command_name, topic)
                    )

        return cli_sections

    def _parse_intro_section(self, section: Tag, command_name: str, topic: str):
        sections = []
        content = {self.DESCRIPTION: [], self.COMMAND_NAME: command_name}
        for child in section.children:
            if not isinstance(child, Tag):
                continue
            sections.extend(self._extract_text_from_tag(child))
        content[self.DESCRIPTION] = list(
            filter(lambda x: x != "", content[self.DESCRIPTION])
        )
        content[self.DESCRIPTION] = list(map(self.sanitize_text, sections))
        content[self.TOPIC] = topic
        return content

    def _parse_detail_section(self, section: Tag, command_name: str, topic: str):
        sections = section.find_all("section")
        (
            description,
            syntax,
            params,
            default_config,
            command_mode,
            user_guidelines,
            examples,
        ) = (None, None, [], None, None, None, None)
        seen_params = set()
        for i, sec in enumerate(sections):
            if i == 0:
                description = self._extract_text(sec)
            elif sec.find(string=re.compile(r"^Syntax", flags=re.I)):
                syntax = self._extract_paragraphs(sec)
            elif sec.find(string=re.compile(r"^Parameters", flags=re.I)):
                params = self._extract_parameters(sec, seen_params)
            elif sec.find(string=re.compile(r"^Default Configuration", flags=re.I)):
                default_config = self._extract_text(sec)
            elif sec.find(string=re.compile(r"^Command Mode", flags=re.I)):
                command_mode = self._extract_text(sec)
            elif sec.find(string=re.compile(r"^User Guidelines", flags=re.I)):
                user_guidelines = self._extract_user_guidelines(sec)
            elif sec.find(string=re.compile(r"^Examples?", flags=re.I)):
                examples = self._extract_examples(sec)

        return {
            self.TOPIC: topic,
            self.COMMAND_NAME: command_name,
            self.DESCRIPTION: (
                self.sanitize_text(description) if description else None
            ),
            self.SYNTAX: list(map(self.sanitize_text, syntax)) if syntax else None,
            self.PARAMETERS: list(map(self.sanitize_text, params)),
            self.DEFAULT_CONFIGURATION: (
                self.sanitize_text(default_config) if default_config else None
            ),
            self.COMMAND_MODE: (
                self.sanitize_text(command_mode) if command_mode else None
            ),
            self.USER_GUIDELINES: (
                self.sanitize_text(user_guidelines) if user_guidelines else None
            ),
            self.EXAMPLES: examples,
        }

    def _extract_text_from_tag(self, tag: Tag) -> List[str]:
        if tag.name == "p":
            return [tag.get_text()]
        elif tag.name == "ul":
            return [li.get_text() for li in tag.find_all("li")]
        elif tag.name == "pre":
            return tag.get_text().split("\n")
        else:
            return [tag.get_text()]

    def _extract_paragraphs(self, section: Tag) -> List[str]:
        return [p.get_text() for p in section.find_all("p")]

    def _extract_parameters(self, section: Tag, seen_params: set) -> List[str]:
        params = []
        p = section.find("p")
        if p is not None:
            text = p.get_text().strip()
            if text not in seen_params:
                seen_params.add(text)
                params.append(text)

        ul = section.find("ul")
        if ul is not None:
            for li in ul.find_all("li"):
                text = li.get_text().strip()
                if text not in seen_params:
                    seen_params.add(text)
                    params.append(text)

        return params

    def _extract_text(self, section: Tag) -> str:
        p = section.find("p")
        return p.get_text() if p else section.get_text()

    def _extract_user_guidelines(self, section: Tag) -> str:
        list_p = section.find_all("p")
        if list_p is not None:
            return " ".join([p.get_text() for p in list_p])
        return section.get_text()

    def _extract_examples(self, section: Tag) -> List[Dict[str, Any]]:
        examples = []
        ex = {}
        description = section.find("p")
        if description:
            ex[self.DESCRIPTION] = self.sanitize_text(description.get_text())
        ul = section.find("ul")
        if ul:
            ex["commands"] = [li.get_text() for li in ul.find_all("li")]
        pre = section.find("pre")
        if pre:
            lines = pre.get_text().split("\n")
            if "commands" in ex:
                ex["commands"].extend(lines)
            else:
                ex["commands"] = lines
        if "commands" in ex:
            ex["commands"] = list(filter(lambda x: x != "", ex["commands"]))
        examples.append(ex)
        return examples


class CiscoSupportingDocumentsLoader(BaseLoader):
    """
    A class for loading Cisco supporting documents, primarily Admin Guide and CLI Guide.

    There are 2 class methods for creating an instance out of convience. \n
    The `from_url` method expects a URL to the main page of the document. \n
    The `from_file` method expects a path to a JSON file containing the documents. If the file does not exist, instance is re-created `from_url`.

    If you pass schema="cli" to the constructor, the loader will parse the CLI Guide documents into a suitable schema for Database storage. This uses the CLIParser class.
    """

    def __init__(
        self,
        paths: List[str],
        schema: Optional[Literal["cli"]] = None,
        doc_type: Optional[str] = None,
    ) -> None:
        self.paths = paths
        self.schema = schema
        self.doc_type = doc_type
        self.documents: List[Union[Document, Dict[str, Any]]] = []

    @classmethod
    def from_url(
        cls,
        url: str,
        schema: Optional[Literal["cli"]] = None,
        doc_type: Optional[str] = None,
    ) -> "CiscoSupportingDocumentsLoader":
        html = cls._make_request(url)
        soup = BeautifulSoup(html, "html.parser")
        paths = cls._extract_paths(soup)
        return cls(paths=paths, schema=schema, doc_type=doc_type)

    @classmethod
    def from_datasheet(cls, url: str) -> "CiscoSupportingDocumentsLoader":
        return cls(paths=[url], schema=None, doc_type="Datasheet")

    @property
    def default_parser(self) -> str:
        return "html.parser"

    @default_parser.setter
    def default_parser(self, parser: str) -> None:
        self._check_parser(parser)
        self.default_parser = parser

    @staticmethod
    def _check_parser(parser: str) -> None:
        """Check that parser is valid for bs4."""
        valid_parsers = ["html.parser", "lxml", "xml", "lxml-xml", "html5lib"]
        if parser not in valid_parsers:
            raise ValueError(
                "`parser` must be one of " + ", ".join(valid_parsers) + "."
            )

    @staticmethod
    def _make_request(url: str) -> str:
        res = requests.get(url)
        res.encoding = "utf-8"
        res.raise_for_status()
        return res.text

    @staticmethod
    def _extract_paths(soup: BeautifulSoup) -> str:
        toc = soup.select("ul#bookToc > li > a")
        links = [f"https://www.cisco.com{link.get('href')}" for link in toc]
        return links

    @staticmethod
    def sanitize_text(text: str) -> str:
        cleaned_text = re.sub(r"\s+", " ", text.strip())
        cleaned_text = cleaned_text.replace("\\", "")
        cleaned_text = cleaned_text.replace("#", " ")
        cleaned_text = re.sub(r"([^\w\s])\1*", r"\1", cleaned_text)
        return cleaned_text

    @staticmethod
    def _build_metadata(soup: BeautifulSoup, url: str, **kwargs) -> Dict[str, str]:
        """Build metadata from BeautifulSoup output.
        Args:
            soup (BeautifulSoup): The BeautifulSoup object containing the parsed HTML.
            url (str): The URL of the source.
            **kwargs: Additional keyword arguments.
        Returns:
            Dict[str, str]: The metadata dictionary containing the extracted information.
        """
        dom = etree.HTML(str(soup))
        metadata = {"source": url}
        if title := soup.find("meta", attrs={"name": "description"}):
            metadata["title"] = title.get("content", "Chapter not found.")
        if html := soup.find("html"):
            metadata["language"] = html.get("lang", "No language found.")
        if concept := soup.find("meta", attrs={"name": "concept"}):
            metadata["concept"] = concept.get("content", "No concept found.")
        if topic := kwargs.get("topic"):
            metadata["topic"] = topic
        if published_date := dom.xpath('//*[@id="documentInfo"]/dl/dd'):
            metadata["published_date"] = published_date[0].text.strip()
        if document_id := soup.find("meta", attrs={"name": "documentId"}):
            metadata["document_id"] = document_id.get(
                "content", "No document ID found."
            )
        metadata["doc_id"] = str(uuid.uuid4())
        return metadata

    def load(self) -> List[Document]:
        return list(self.lazy_load())

    def lazy_load(self) -> Iterator[Union[Document, Dict[str, Any]]]:
        for path in self.paths:
            yield from self._fetch(path)

    def _fetch(self, path: str):
        print(f"Fetching document from {path}")
        html = self._make_request(path)
        soup = BeautifulSoup(html, "html.parser")

        if self.schema == "cli":
            parser = CLIParser()
            data = parser.load(soup)
            metadata = [self._build_metadata(soup, path) for _ in data]
            # merge metadata and data
            for d, m in zip(data, metadata):
                if self.doc_type:
                    m["doc_type"] = self.doc_type
                merged = {**d, **m}
                self.documents.append(merged)
                yield merged
        else:
            data = self._parse(soup)
            metadata = [
                self._build_metadata(soup, path, topic=d["topic"]) for d in data
            ]
            ids = [str(uuid.uuid4()) for _ in range(len(data))]
            for d, m, i in zip(data, metadata, ids):
                if re.match(
                    r"^This chapter contains the following sections:", d["text"]
                ):
                    continue
                if self.doc_type:
                    m["doc_type"] = self.doc_type
                document = Document(page_content=d["text"], metadata=m, id=i)
                self.documents.append(document)
                yield document

    def _parse(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """This method is useful for parsing the content of the Admin Guide or CLI Guide into a large chunk of text and topics suitable for LCEL Documents"""
        topic_sections = soup.find_all("section", class_=("body"))

        return [
            {
                "topic": f"{section.find_previous('h2', class_='title').get_text(strip=True) if section.find_previous('h2', class_='title') else ''} {section.find_previous_sibling('h3', class_='title').get_text(strip=True) if section.find_previous_sibling('h3', class_='title') else ''}".strip(),
                "text": self.sanitize_text(section.get_text()),
            }
            for section in topic_sections
        ]

    def dump_json(self, path: Union[Path, str]) -> None:
        try:
            if isinstance(path, str):
                path = Path(path)
            with path.open("w", encoding="utf-8") as f:
                json.dump(
                    [
                        doc.dict() if isinstance(doc, Document) else doc
                        for doc in self.documents
                    ],
                    f,
                    indent=2,
                    ensure_ascii=True,
                )
        except Exception as e:
            logger.error(f"An error occurred while dumping the JSON file: {e}")

    @classmethod
    def from_file(
        cls, path: Union[Path, str], url: str, schema: Optional[Literal["cli"]] = None
    ) -> "CiscoSupportingDocumentsLoader":
        try:
            if isinstance(path, str):
                path = Path(path)
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            instance = cls(paths=[], schema=schema)
            instance.documents = [
                (
                    Document.parse_obj(doc)
                    if "type" in doc and doc["type"] == "Document"
                    else doc
                )
                for doc in data
            ]
            return instance
        except (json.JSONDecodeError, FileNotFoundError):
            logger.info(
                f"\n"
                f"File not found at {path}. Recreating the data from URL {url}."
                f"Recreating the data from URL {url}."
                f"Returning cls.from_url(url, schema=schema)"
            )
            return cls.from_url(url, schema=schema)
        except Exception as e:
            logger.info(
                f"An error occurred while loading the JSON file: {e}\n"
                f"Returning cls.from_url(url, schema=schema)"
            )
            return cls.from_url(url, schema=schema)


######################
# Loads the documents into ChromaDB
# Chunks must be > 8192 tokens
######################

FAMILIES = {
    # "Cisco Business 220 Series Smart Switches": {
    #     "ag": "https://www.cisco.com/c/en/us/td/docs/switches/lan/csbss/CBS220/Adminstration-Guide/cbs-220-admin-guide.html",
    #     "cli": "https://www.cisco.com/c/en/us/td/docs/switches/lan/csbss/CBS220/CLI-Guide/b_220CLI.html",
    # },
    # "Cisco Business 250 Series Smart Switches": {
    #     "ag": "https://www.cisco.com/c/en/us/td/docs/switches/lan/csbms/CBS_250_350/Administration-Guide/cbs-250-ag.html",
    #     "cli": "https://www.cisco.com/c/en/us/td/docs/switches/lan/csbms/CBS_250_350/CLI/cbs-250-cli.html",
    # },
    # "Cisco Business 350 Series Managed Switches": {
    #     "ag": "https://www.cisco.com/c/en/us/td/docs/switches/lan/csbms/CBS_250_350/Administration-Guide/cbs-350.html",
    #     "cli": "https://www.cisco.com/c/en/us/td/docs/switches/lan/csbms/CBS_250_350/CLI/cbs-350-cli-.html",
    # },
    # "Cisco 350 Series Managed Switches": {
    #     "ag": "https://www.cisco.com/c/en/us/td/docs/switches/lan/csbms/350xseries/2_5_7/Administration/tesla-350-550.html",
    #     "cli": "https://www.cisco.com/c/en/us/td/docs/switches/lan/csbms/CBS_250_350/CLI/cbs-350-cli-.html",
    # },
    # "Cisco 350X Series Stackable Managed Switches": {
    #     "ag": "https://www.cisco.com/c/en/us/td/docs/switches/lan/csbms/350xseries/2_5_7/Administration/tesla-350-550.html",
    #     "cli": "https://www.cisco.com/c/en/us/td/docs/switches/lan/csbms/CBS_250_350/CLI/cbs-350-cli-.html",
    # },
    # "Cisco 550X Series Stackable Managed Switches": {
    #     "ag": "https://www.cisco.com/c/en/us/td/docs/switches/lan/csbms/350xseries/2_5_7/Administration/tesla-350-550.html",
    #     "cli": "https://www.cisco.com/c/en/us/td/docs/switches/lan/csbms/CBS_250_350/CLI/cbs-350-cli-.html",
    # },
    "Cisco Catalyst 1200 Series Switches": {
        "ag": "https://www.cisco.com/c/en/us/td/docs/switches/campus-lan-switches-access/Catalyst-1200-and-1300-Switches/Admin-Guide/catalyst-1200-admin-guide.html",
        "cli": "https://www.cisco.com/c/en/us/td/docs/switches/campus-lan-switches-access/Catalyst-1200-and-1300-Switches/cli/C1200-cli.html",
    },
    "Cisco Catalyst 1300 Series Switches": {
        "ag": "https://www.cisco.com/c/en/us/td/docs/switches/campus-lan-switches-access/Catalyst-1200-and-1300-Switches/Admin-Guide/catalyst-1300-admin-guide.html",
        "cli": "https://www.cisco.com/c/en/us/td/docs/switches/campus-lan-switches-access/Catalyst-1200-and-1300-Switches/cli/C1300-cli.html",
    },
}

SERIES_DOCUMENT_MAP: SourceMap = {
    "Cisco Business 220 Series Smart Switches": {
        "ag": (
            CBS_220_ADMIN_GUIDE_COLLECTION,
            "https://www.cisco.com/c/en/us/td/docs/switches/lan/csbss/CBS220/Adminstration-Guide/cbs-220-admin-guide.html",
        ),
        "cli": (
            CBS_220_CLI_GUIDE_COLLECTION,
            "https://www.cisco.com/c/en/us/td/docs/switches/lan/csbss/CBS220/CLI-Guide/b_220CLI.html",
        ),
    },
    "Cisco Business 250 Series Smart Switches": {
        "ag": (
            CBS_250_ADMIN_GUIDE_COLLECTION,
            "https://www.cisco.com/c/en/us/td/docs/switches/lan/csbms/CBS_250_350/Administration-Guide/cbs-250-ag.html",
        ),
        "cli": (
            CBS_250_CLI_GUIDE_COLLECTION,
            "https://www.cisco.com/c/en/us/td/docs/switches/lan/csbms/CBS_250_350/CLI/cbs-250-cli.html",
        ),
    },
    "Cisco Business 350 Series Managed Switches": {
        "ag": (
            CBS_350_ADMIN_GUIDE_COLLECTION,
            "https://www.cisco.com/c/en/us/td/docs/switches/lan/csbms/CBS_250_350/Administration-Guide/cbs-350.html",
        ),
        "cli": (
            CBS_350_CLI_GUIDE_COLLECTION,
            "https://www.cisco.com/c/en/us/td/docs/switches/lan/csbms/CBS_250_350/CLI/cbs-350-cli-.html",
        ),
    },
    "Cisco Business 350 Series Managed Switches": {
        "ag": (
            CBS_350_ADMIN_GUIDE_COLLECTION,
            "https://www.cisco.com/c/en/us/td/docs/switches/lan/csbms/CBS_250_350/Administration-Guide/cbs-350.html",
        ),
        "cli": (
            CBS_350_CLI_GUIDE_COLLECTION,
            "https://www.cisco.com/c/en/us/td/docs/switches/lan/csbms/CBS_250_350/CLI/cbs-350-cli-.html",
        ),
    },
    "Cisco 350 Series Managed Switches": {
        "ag": (
            CISCO_350_ADMIN_GUIDE_COLLECTION,
            "https://www.cisco.com/c/en/us/td/docs/switches/lan/csbms/350xseries/2_5_7/Administration/tesla-350-550.html",
        ),
        "cli": (
            CISCO_350_CLI_GUIDE_COLLECTION_NAME,
            "https://www.cisco.com/c/en/us/td/docs/switches/lan/csbms/CBS_250_350/CLI/cbs-350-cli-.html",
        ),
    },
    "Cisco 350X Series Stackable Managed Switches": {
        "ag": (
            CISCO_350X_ADMIN_GUIDE_COLLECTION_NAME,
            "https://www.cisco.com/c/en/us/td/docs/switches/lan/csbms/350xseries/2_5_7/Administration/tesla-350-550.html",
        ),
        "cli": (
            CISCO_350X_CLI_GUIDE_COLLECTION_NAME,
            "https://www.cisco.com/c/en/us/td/docs/switches/lan/csbms/CBS_250_350/CLI/cbs-350-cli-.html",
        ),
    },
    "Cisco 550X Series Stackable Managed Switches": {
        "ag": (
            CISCO_550X_ADMIN_GUIDE_COLLECTION_NAME,
            "https://www.cisco.com/c/en/us/td/docs/switches/lan/csbms/350xseries/2_5_7/Administration/tesla-350-550.html",
        ),
        "cli": (
            CISCO_550X_CLI_GUIDE_COLLECTION_NAME,
            "https://www.cisco.com/c/en/us/td/docs/switches/lan/csbms/CBS_250_350/CLI/cbs-350-cli-.html",
        ),
    },
    "Cisco 350 Series Managed Switches": {
        "ag": (
            CISCO_350_ADMIN_GUIDE_COLLECTION,
            "https://www.cisco.com/c/en/us/td/docs/switches/lan/csbms/350xseries/2_5_7/Administration/tesla-350-550.html",
        ),
        "cli": (
            CISCO_350_CLI_GUIDE_COLLECTION_NAME,
            "https://www.cisco.com/c/en/us/td/docs/switches/lan/csbms/CBS_250_350/CLI/cbs-350-cli-.html",
        ),
    },
    "Cisco Catalyst 1200 Series Switches": {
        "ag": (
            CATALYST_1200_ADMIN_GUIDE_COLLECTION,
            "https://www.cisco.com/c/en/us/td/docs/switches/campus-lan-switches-access/Catalyst-1200-and-1300-Switches/Admin-Guide/catalyst-1200-admin-guide.html",
        ),
        "cli": (
            CATALYST_1200_CLI_GUIDE_COLLECTION,
            "https://www.cisco.com/c/en/us/td/docs/switches/campus-lan-switches-access/Catalyst-1200-and-1300-Switches/cli/C1200-cli.html",
        ),
    },
    "Cisco Catalyst 1300 Series Switches": {
        "ag": (
            CATALYST_1300_ADMIN_GUIDE_COLLECTION,
            "https://www.cisco.com/c/en/us/td/docs/switches/campus-lan-switches-access/Catalyst-1200-and-1300-Switches/Admin-Guide/catalyst-1300-admin-guide.html",
        ),
        "cli": (
            CATALYST_1300_CLI_GUIDE_COLLECTION,
            "https://www.cisco.com/c/en/us/td/docs/switches/campus-lan-switches-access/Catalyst-1200-and-1300-Switches/cli/C1300-cli.html",
        ),
    },
}

tokenizer = GPT2Tokenizer.from_pretrained("gpt2")


def count_tokens(text: str) -> int:
    return len(tokenizer.encode(text))


def split_text(text: str, max_tokens: int = MAX_TOKENS) -> List[str]:
    sentences = text.split(".")
    current_chunk = []
    chunks = []
    current_tokens = 0
    for sentence in sentences:
        sentence_tokens = count_tokens(sentence)
        if current_tokens + sentence_tokens > max_tokens:
            chunks.append(".".join(current_chunk))
            current_chunk = [sentence]
            current_tokens = sentence_tokens
        else:
            current_chunk.append(sentence)
            current_tokens += sentence_tokens
    if current_chunk:
        chunks.append(".".join(current_chunk))

    return chunks


def load_documents(loader: CiscoSupportingDocumentsLoader) -> List[Document]:
    if len(loader.documents) == 0:
        return loader.load()
    return loader.documents


def process_documents(docs: List[Document], doc_type: str):
    for doc in docs:
        doc.metadata["doc_type"] = doc_type


def process_and_insert_documents(
    url: str, collection_name: str, doc_type: str, embedding_func: str
):
    if collection_name.endswith("_openai"):
        name = collection_name[:-7]
    elif collection_name.endswith("_huggingface"):
        name = collection_name[:-13]
    else:
        name = collection_name

    file_path = f"{BASE_DIR}/backend/data/cisco/documents/{name}.json"
    loader = CiscoSupportingDocumentsLoader.from_file(file_path, url)
    docs = load_documents(loader)
    process_documents(docs, doc_type)
    loader.dump_json(f"{BASE_DIR}/backend/data/cisco/documents/{collection_name}.json")
    load_docs_chroma(docs, collection_name, embedding_func)


def load_docs_chroma(documents, collection_name, embedding_func: str):
    docs = documents
    print(f"Loaded {len(docs)} documents from {collection_name}.json")
    content: list[str] = [doc.page_content for doc in docs]  # Langchain Document Schema
    ids: list[str] = [doc.metadata["doc_id"] for doc in docs]
    metadatas = [doc.metadata for doc in docs]

    if embedding_func == "openai":
        collection = CHROMA_CLIENT.get_or_create_collection(
            name=collection_name, embedding_function=openai_embeddings
        )
    elif embedding_func == "huggingface":
        collection = CHROMA_CLIENT.get_or_create_collection(
            name=collection_name,
            embedding_function=sentence_all_MiniLM_V6_v2_embeddings,
        )
    else:
        raise ValueError("Invalid embedding function")

    # collection = CHROMA_CLIENT.get_or_create_collection(
    #     name=collection_name, embedding_function=openai_embeddings
    # )

    for doc_id, doc_content, metadata in zip(ids, content, metadatas):
        if count_tokens(doc_content) > MAX_TOKENS:
            truncated_content = tokenizer.decode(
                tokenizer.encode(doc_content)[:MAX_TOKENS],
                clean_up_tokenization_spaces=True,
            )
            logger.info(
                f"Document {doc_id} has more than {MAX_TOKENS} tokens. Truncated content to {len(truncated_content)} tokens."
            )
            try:
                collection.add(
                    ids=[doc_id],
                    documents=split_text(truncated_content),
                    metadatas=[metadata],
                )
            except ValueError as e:
                logger.warning(f"Most likely found a duplicate ID: {e}")
                new_id = str(uuid.uuid4())
                collection.add(
                    ids=[new_id],
                    documents=split_text(truncated_content),
                    metadatas=[metadata],
                )
        else:
            try:
                collection.add(
                    ids=[doc_id], documents=[doc_content], metadatas=[metadata]
                )
            except ValueError as e:
                logger.warning(f"Most likely found a duplicate ID: {e}")
                new_id = str(uuid.uuid4())
                collection.add(
                    ids=[new_id], documents=[doc_content], metadatas=[metadata]
                )


def get_or_create_collections(admin_guide, cli_guide):
    try:
        admin_guide_collection = CHROMA_CLIENT.get_collection(admin_guide)
        cli_guide_collection = CHROMA_CLIENT.get_collection(cli_guide)
        ag_docs = admin_guide_collection.get()
        cli_docs = cli_guide_collection.get()
        if admin_guide_collection and cli_guide_collection:
            if len(ag_docs) > 0 and len(cli_docs) > 0:
                # move to next iteration
                logger.info(
                    f"Collection for {admin_guide} and {cli_guide} already exists. Skipping."
                )
                return True
            else:
                logger.info(
                    f"Collection for {admin_guide} and {cli_guide} exists but is empty. Proceeding to load documents."
                )
                CHROMA_CLIENT.delete_collection(admin_guide)
                CHROMA_CLIENT.delete_collection(cli_guide)
                CHROMA_CLIENT.get_or_create_collection(admin_guide)
                CHROMA_CLIENT.get_or_create_collection(cli_guide)
                return False
    except ValueError:
        logger.info(
            f"Error retrieving collection for {admin_guide} or {cli_guide}. Creating new collections."
        )

        CHROMA_CLIENT.get_or_create_collection(admin_guide)
        CHROMA_CLIENT.get_or_create_collection(cli_guide)
        return False
        # do nothing


def prepare_collections():
    for series, sources in FAMILIES.items():
        print(f"Processing for {series} assets...")
        ag_url = sources["ag"]
        cli_url = sources["cli"]

        openai_collections_class = CollectionFactory.get_collections("openai")
        openai_admin_guide_coll, openai_cli_guide_coll = (
            openai_collections_class.resolve_collection_name(series)
        )
        huggingface_collections_class = CollectionFactory.get_collections("huggingface")
        huggingface_admin_guide_coll, huggingface_cli_guide_coll = (
            huggingface_collections_class.resolve_collection_name(series)
        )

        if openai_admin_guide_coll and openai_cli_guide_coll:
            already_exists = get_or_create_collections(
                openai_admin_guide_coll, openai_cli_guide_coll
            )
            if already_exists:
                continue
        if huggingface_admin_guide_coll and huggingface_cli_guide_coll:
            already_exists = get_or_create_collections(
                huggingface_admin_guide_coll, huggingface_cli_guide_coll
            )
            if already_exists:
                continue
        process_and_insert_documents(
            ag_url, openai_admin_guide_coll, "AdminGuide", "openai"
        )
        process_and_insert_documents(
            cli_url, openai_cli_guide_coll, "CLIGuide", "openai"
        )
        process_and_insert_documents(
            ag_url, huggingface_admin_guide_coll, "AdminGuide", "huggingface"
        )
        process_and_insert_documents(
            cli_url, huggingface_cli_guide_coll, "CLIGuide", "huggingface"
        )

    # for series, sources in SERIES_DOCUMENT_MAP.items():
    #     print(f"Processing for {series} assets")
    #     ag_collection_name, ag_url = sources["ag"]
    #     cli_collection_name, cli_url = sources["cli"]

    #     try:
    #         ag_collection = CHROMA_CLIENT.get_collection(ag_collection_name)
    #         cli_collection = CHROMA_CLIENT.get_collection(cli_collection_name)

    #         if ag_collection and cli_collection:
    #             # move to next iteration
    #             logger.info(
    #                 f"Collection for {ag_collection_name} and {cli_collection_name} already exists. Skipping."
    #             )
    #             continue
    #     except ValueError:
    #         logger.info(
    #             f"Error retrieving collection for {ag_collection_name} or {cli_collection_name}. Creating new collections."
    #         )

    #         CHROMA_CLIENT.get_or_create_collection(ag_collection_name)
    #         CHROMA_CLIENT.get_or_create_collection(cli_collection_name)
    #         # do nothing

    #     process_and_insert_documents(ag_url, ag_collection_name, "AdminGuide")
    #     process_and_insert_documents(cli_url, cli_collection_name, "CLIGuide")


def run():
    prepare_collections()


def query_collection(query: str):
    from langchain_openai.embeddings import OpenAIEmbeddings
    from langchain_huggingface.embeddings import HuggingFaceEmbeddings

    try:
        openai_collection = CHROMA_CLIENT.get_collection(
            "catalyst_1300_admin_guide_openai"
        )
        openai_embeddings = OpenAIEmbeddings(api_key=os.environ.get("OPENAI_API_KEY"))
        openai_query = openai_embeddings.embed_query(query)
        openai_results = openai_collection.query(openai_query)
        logger.info(f"Query: {query}\nResults: {openai_results}")

        hf_collection = CHROMA_CLIENT.get_collection(
            "catalyst_1300_admin_guide_huggingface"
        )
        e = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        hf_query = e.embed_query(query)
        # Add debugging statements
        logger.debug(f"Type of hf_query: {type(hf_query)}")
        logger.debug(f"Content of hf_query: {hf_query}")
        hf_results = hf_collection.query(
            query_embeddings=hf_query,
            include=["embeddings", "metadatas", "documents", "distances"],
        )
        logger.info(f"Query: {query}\nResults: {hf_results}")
    except Exception as e:
        logger.error(f"An error occurred while querying the collection: {e}")
        return None


if __name__ == "__main__":
    # run()
    query = "RADIUS and Duo Authentication"
    results = query_collection(query)
