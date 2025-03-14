import os
import uuid
import json
import pymongo
import pymongo.errors
import logging
import markdown
import time
from collections import defaultdict
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv, find_dotenv
from pprint import pprint
from huggingface_hub import snapshot_download
from typing import Dict, List, Any, Optional, Literal, Tuple
from chromadb.api.types import GetResult
from chromadb import Collection as Coll
from apps.webui.models.articles import (
    CreatedArticle,
    DataSourceType,
    Search,
    GraphState,
    Grader,
    Step,
    Steps,
)
from apps.cisco.examples import create_decomposition_search_examples

from apps.cisco.utils import (
    remove_props_from_dict,
    tool_example_to_messages_helper,
)
from config import (
    BASE_DIR,
    DATA_DIR,
    CHROMA_CLIENT,
    CollectionFactory,
)
from langchain.output_parsers.openai_tools import PydanticToolsParser
from langchain.storage.in_memory import InMemoryStore
from langchain.schema import Document
from langchain.retrievers.parent_document_retriever import ParentDocumentRetriever
from langchain.retrievers.multi_vector import SearchType
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.chains.query_constructor.base import AttributeInfo
from langchain_core.output_parsers import StrOutputParser
from langchain_core.language_models import BaseLanguageModel
from langchain_core.utils.function_calling import convert_to_openai_tool
from langchain_core.runnables import RunnablePassthrough
from langchain_core.retrievers import BaseRetriever
from langchain_core.vectorstores import VectorStore
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import END, StateGraph
from config import MONGODB_URI, MONGODB_USER, MONGODB_PASS
import sys

from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun

import operator

from typing import Optional, Sequence

from langchain_core.documents import BaseDocumentCompressor, Document
from langchain_core.callbacks import Callbacks, CallbackManagerForRetrieverRun
from langchain_community.retrievers import BM25Retriever
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.retrievers import EnsembleRetriever, ContextualCompressionRetriever
from pydantic import BaseModel
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain.retrievers.document_compressors.cross_encoder import BaseCrossEncoder
from langchain.retrievers.multi_vector import MultiVectorRetriever
from langchain.storage import InMemoryByteStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info(f"Logger name: {logger.name}")
logger.info(f"Logger level: {logger.level}")
logger.info(f"Module: {__name__}")


SEPARATOR_NUM = 50


class RerankCompressor(BaseDocumentCompressor):
    embedding_function: HuggingFaceEmbeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    top_n: int
    reranking_function: HuggingFaceCrossEncoder = HuggingFaceCrossEncoder()
    r_score: float

    class Config:
        extra = "forbid"
        arbitrary_types_allowed = True

    def compress_documents(
        self,
        documents: Sequence[Document],
        query: str,
        callbacks: Optional[Callbacks] = None,
    ) -> Sequence[Document]:

        scores = self.reranking_function.score(
            [(query, doc.page_content) for doc in documents]
        )

        docs_with_scores = list(zip(documents, scores))
        if self.r_score:
            docs_with_scores = [
                (d, s) for d, s in docs_with_scores if s >= self.r_score
            ]

        result = sorted(docs_with_scores, key=operator.itemgetter(1), reverse=True)
        final_results = []
        for doc, doc_score in result[: self.top_n]:
            metadata = doc.metadata
            metadata["score"] = doc_score
            doc = Document(
                page_content=doc.page_content,
                metadata=metadata,
            )
            final_results.append(doc)
        return final_results


class ChromaRetriever(BaseRetriever):
    collection: Coll
    embedding_function: Any
    top_n: int

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: CallbackManagerForRetrieverRun,
    ) -> List[Document]:
        query_embeddings = self.embedding_function.embed_query(query)

        results = self.collection.query(
            query_embeddings=[query_embeddings],
            n_results=self.top_n,
        )

        ids = results["ids"][0]
        metadatas = results["metadatas"][0]
        documents = results["documents"][0]

        results = []
        for idx in range(len(ids)):
            results.append(
                Document(
                    metadata=metadatas[idx],
                    page_content=documents[idx],
                )
            )
        return results


def get_model_path(model: str, update_model: bool = False):
    # Construct huggingface_hub kwargs with local_files_only to return the snapshot path
    cache_dir = os.getenv("SENTENCE_TRANSFORMERS_HOME")

    local_files_only = not update_model

    snapshot_kwargs = {
        "cache_dir": cache_dir,
        "local_files_only": local_files_only,
    }

    logger.debug(f"model: {model}")
    logger.debug(f"snapshot_kwargs: {snapshot_kwargs}")

    # Inspiration from upstream sentence_transformers
    if (
        os.path.exists(model)
        or ("\\" in model or model.count("/") > 1)
        and local_files_only
    ):
        # If fully qualified path exists, return input, else set repo_id
        return model
    elif "/" not in model:
        # Set valid repo_id for model short-name
        model = "sentence-transformers" + "/" + model

    snapshot_kwargs["repo_id"] = model

    # Attempt to query the huggingface_hub library to determine the local path and/or to update
    try:
        model_repo_path = snapshot_download(**snapshot_kwargs)
        logger.debug(f"model_repo_path: {model_repo_path}")
        return model_repo_path
    except Exception as e:
        logger.exception(f"Cannot determine model snapshot path: {e}")
        return model


def query_doc_with_hybrid_search(
    collection_name: str,
    query: str,
    embedding_function=HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    ),
    k: int = 4,
    reranking_function=HuggingFaceCrossEncoder(model_name="BAAI/bge-reranker-v2-m3"),
    r: float = 0.0,
):
    logger.debug("Running query_doc_with_hybrid_search")
    try:
        collection = CHROMA_CLIENT.get_collection(name=collection_name)
        documents = collection.get()  # get all documents

        bm25_retriever = BM25Retriever.from_texts(
            texts=documents.get("documents"),
            metadatas=documents.get("metadatas"),
        )
        bm25_retriever.k = k
        chroma_retriever = ChromaRetriever(
            collection=collection,
            embedding_function=embedding_function,
            top_n=k,
        )

        ensemble_retriever = EnsembleRetriever(
            retrievers=[bm25_retriever, chroma_retriever], weights=[0.5, 0.5]
        )

        compressor = RerankCompressor(
            embedding_function=embedding_function,
            top_n=k,
            reranking_function=reranking_function,
            r_score=r,
        )

        compression_retriever = ContextualCompressionRetriever(
            base_compressor=compressor, base_retriever=ensemble_retriever
        )
        # chroma = Chroma(
        #     collection_name=collection_name, embedding_function=embedding_function
        # )
        # chroma.add_documents(convert_to_documents(documents))
        # chroma_retriever = chroma.as_retriever(search_kwargs={"k": k})
        # ensemble_retriever = EnsembleRetriever(
        #     retrievers=[bm25_retriever, chroma_retriever], weights=[0.5, 0.5]
        # )
        result = compression_retriever.invoke(query)

        logger.info(f"query_doc_with_hybrid_search:result {result}")
        return result
    except Exception as e:
        raise e


load_dotenv(find_dotenv(filename=".env"))

try:
    mongo_client = MongoClient(
        MONGODB_URI.replace("<username>", MONGODB_USER).replace(
            "<password>", MONGODB_PASS
        )
    )
    logger.info("Connected to MongoDB Atlas")
except pymongo.errors.ConfigurationError as e:
    logger.error(f"Error connecting to MongoDB Atlas: {e}")
    logger.error(
        "An Invalid URI host error was received. Is your Atlas host name correct in your connection string?"
    )
    sys.exit(1)


def setup_chat_openai(
    model: str = "gpt-4o", temperature: int = 0, verbose: bool = True
):
    return ChatOpenAI(model=model, temperature=temperature, verbose=verbose)


def format_docs(documents: List[Document]) -> str:
    """
    Formats a list of documents into a single string with separators.

    Args:
        documents (List[Document]): A list of Document objects to format.

    Returns:
        str: A formatted string representation of the documents.
    """
    return f"\n{'-' * SEPARATOR_NUM}\n".join(
        [f"Document {i+1}:\n\n" + doc.page_content for i, doc in enumerate(documents)]
    )


def format_other_sources(sources: List[str]) -> str:
    return f"\n{'-' * SEPARATOR_NUM}\n".join(
        [f"Source {i+1}:\n\n" + source for i, source in enumerate(sources)]
    )


def convert_to_documents(results: GetResult) -> List[Document]:
    """
    Converts results from a database query into a list of Document objects.

    Args:
        results (GetResult): The results from a database query, containing documents and metadata.

    Returns:
        List[Document]: A list of Document objects.
    """
    return [
        Document(page_content=doc, metadata=meta)
        for doc, meta in zip(results.get("documents"), results.get("metadatas"))
    ]


def get_text_splitter(
    chunk_size: int = 300, chunk_overlap: int = 0, add_start_index: bool = False
) -> RecursiveCharacterTextSplitter:
    """
    Returns a configured RecursiveCharacterTextSplitter instance.

    Returns:
        RecursiveCharacterTextSplitter: Text splitter configured for chunking text.
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        add_start_index=add_start_index,
    )


def query_database(
    collection_name: str,
    ids: Optional[List[str]] = None,
    where: Optional[Dict[str, Any]] = None,
) -> GetResult:
    """
    Fetches results from a database collection based on provided criteria.

    Args:
        collection_name (str): The name of the collection to query.
        ids (Optional[List[str]]): A list of document IDs to fetch.
        where (Optional[Dict[str, Any]]): A dictionary specifying query conditions.

    Returns:
        GetResult: The results from the database query.
    """
    collection = CHROMA_CLIENT.get_or_create_collection(name=collection_name)
    arguments = {}
    if ids:
        arguments["ids"] = ids
    if where:
        arguments["where"] = where
    try:
        docs = collection.get(**arguments)
    except Exception as e:
        logger.error(f"Failed to get documents from collection {collection_name}: {e}")
        docs = {"documents": [], "metadatas": []}
    return docs


def create_or_retrieve_db(
    collection_name: str, persist_dir: Optional[str] = f"{DATA_DIR}/langchain_vector_db"
) -> Chroma:
    """
    Creates or retrieves a LangChain vector database.

    Args:
        collection_name (str): The name of the collection.
        persist_dir (Optional[str]): The directory to persist the database.

    Returns:
        Chroma: The LangChain vector database.
    """
    return Chroma(
        collection_name=f"langchain_{collection_name}",
        embedding_function=HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        ),
        persist_directory=persist_dir,
    )


def init_self_query_retriever(
    llm: BaseLanguageModel,
    vectordb: VectorStore,
    doc_contents: str,
    collection_name: str,
):
    """
    Initialize a self-query retriever for the given params.

    Args:
        llm (BaseLanguageModel): The language model to use
        vectordb (VectorStore): The vector store to use
        doc_contents (str): Description of the document contents
        collection_name (str): The name of the Chroma collection to use

    Returns:
        SelfQueryRetriever: The initialized self-query retriever
    """
    docs = query_database(collection_name=collection_name)
    documents = convert_to_documents(docs)
    cli_titles = list(set([doc["title"] for doc in docs["metadatas"]]))
    concepts = list(set([doc["concept"] for doc in docs["metadatas"]]))
    metadata_field_info = [
        AttributeInfo(
            name="title",
            description=f"Describes the primary focus or topic of the document. One of {cli_titles}",
            type="string",
        ),
        AttributeInfo(
            name="source",
            description="The URL where the document can be accessed, indicating the location of the online resource within Cisco's documentation system.",
            type="string",
        ),
        AttributeInfo(
            name="concept",
            description=f"Identifies the Product Family name. One of {concepts}",
            type="string",
        ),
        AttributeInfo(
            name="topic",
            description="The topic of the document, which is a more specific description of the document's content.",
            type="string",
        ),
        AttributeInfo(
            name="language",
            description="Indicates the language of the document.",
            type="string",
        ),
        AttributeInfo(
            name="doc_id",
            description="A unique identifier for the document used within a content management system for tracking, management, and retrieval purposes.",
            type="string",
        ),
    ]
    self_query_retriever = SelfQueryRetriever.from_llm(
        llm=llm,
        vectorstore=vectordb,
        document_contents=doc_contents,
        metadata_field_info=metadata_field_info,
        verbose=True,
    )

    self_query_retriever.vectorstore.add_documents(documents)
    return self_query_retriever


def init_parent_document_retriever(collection_name: str):
    """
    Initialize a parent document retriever for the given collection.

    Args:
        collection_name (str): The name of the collection to use.

    Returns:
        ParentDocumentRetriever: The parent document retriever instance.
    """

    lc_vector_db = create_or_retrieve_db(collection_name)
    id_key = "doc_id"
    docstore = InMemoryStore()
    retriever = ParentDocumentRetriever(
        vectorstore=lc_vector_db,
        docstore=docstore,
        id_key=id_key,
        child_splitter=RecursiveCharacterTextSplitter(
            chunk_size=300, chunk_overlap=0, add_start_index=True
        ),
        search_type=SearchType.similarity,
        search_kwargs={"k": 3},
    )

    try:
        collection = CHROMA_CLIENT.get_collection(name=collection_name)
    except Exception as e:
        raise ValueError(f"Failed to get collection {collection_name}: {e}")

    docs = convert_to_documents(collection.get())
    ids: List[str] = [doc.metadata.get(id_key) for doc in docs]

    retriever.add_documents(docs, ids)
    # Smoketest to check large and small chunks
    # Retriever should return the large chunks
    # Vectorstore should return the small chunks
    large_chunks = retriever.invoke("Smartport Features")
    print(
        f'Large Chunks Documents: {" ".join([doc.page_content for doc in large_chunks])}'
    )
    print(f"Large Chunks: {len(large_chunks[0].page_content)}")
    small_chunks = retriever.vectorstore.similarity_search("Smartport Features", k=3)
    print(f"Small Chunks: {len(small_chunks[0].page_content)}")
    print("Store Length of Keys " + str(len(list(docstore.yield_keys()))))
    print(f"Chroma DB Documents {len(collection.get().get('documents'))}")
    # Print the length of documents in the vectorstore
    print("Length of Formatted Docs" + str(len(docs)))
    return retriever


def decompose_question(
    question: str, retriever: ParentDocumentRetriever | SelfQueryRetriever
) -> Tuple[List[str], List[Document]]:
    examples = create_decomposition_search_examples()
    example_messages = [
        msg for ex in examples for msg in tool_example_to_messages_helper(ex)
    ]
    system = """
        You are an expert at converting user question into database queries. You have access to a database of documents that contain information about configuring a Cisco Switch, Cisco Router, or Cisco Wireless Access Point.
        
        Perform query decomposition. Given a user question, break it down into subtopics which will help answer questions about the main topic or prerequisites to the main topic/question.
        Each subtopic should be about a single concept/fact/idea. The subtopic should be other configurations, commands, or settings that are requirements to the main topic/question.
        
        If there are acronyms or words you are not familiar with, do not try to rephrase them."""
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system),
            MessagesPlaceholder("examples"),
            ("human", "{question}"),
        ]
    )
    query_analyzer = (
        {"question": RunnablePassthrough()}
        | prompt.partial(examples=example_messages)
        | setup_chat_openai().with_structured_output(Search)
    )
    answer = query_analyzer.invoke(question)
    expanded_questions = [query for query in answer.subtopics]
    expanded_questions.append(question)  # Add the original question
    print(f"Queries: {expanded_questions}")
    documents = []
    for query in expanded_questions:
        documents.extend(retriever.invoke(query, kwargs={"k": 3}))
    return expanded_questions, documents


def search_vector_db(
    queries: List[str], retriever: ParentDocumentRetriever | SelfQueryRetriever
) -> List[Document]:
    documents = []
    for query in queries:
        documents.extend(retriever.invoke(query, kwargs={"k": 3}))
    return documents


def db_aggregate(collection_name: str, query):
    """
    Perform an aggregation query on a MongoDB collection.
    Args:
        collection_name (str): The name of the collection to perform the aggregation on.
        query (List[Dict]): The aggregation query to perform.
    Returns:
        List[Dict]: The results of the aggregation query.
    """
    db = mongo_client.get_database("smb_documents")
    collection = db.get_collection(collection_name)
    documents = collection.aggregate(query)
    return list(documents)


def test_prompt_template(datasource: Literal["ADMIN_GUIDE", "CLI_GUIDE"]):
    """
    Selects the appropriate template given the datasource.

    Args:
        datasource (ADMIN_GUIDE or CLI_GUIDE): The preferred method of enacting a device configuration given by the user.

    Returns:
        str: The prompt template to use.
    """
    if datasource == "ADMIN_GUIDE":
        return """Role: You are a Cisco TAC Engineer with extensive technical knowledge about network switches, routers, access points, phones, and network management tools.
    
    You will be given data in XML Format.
    
    Your task is to generate a step-by-step guide for configuring a specific feature on a Cisco network device. Use the question as the configuration topic. 
    
    Use the subtopics provided to help guide the list of step sections. If you do not have context for a subtopic, ignore that entry.
    
    Personalize the article for the device mentioned in XML-Style Tag device.
    
    Only use the context as your knowledge base to generate the article. Use each document sufficiently and pay attention to the order you are guiding the user. For example, before configuring Link Aggregation Control Protocol the user must first Configure the Link Aggregation Settings. 
    
    Ensure step text is written in Markdown.
          
    <device>
        {device}
    </device>
    
    <question>
        {question}
    </question>
    
    <subtopics>
        {subtopics}
    </subtopics>
    
    <rules>
        1. The first step should always be "Log in to the web user interface (UI) of your switch". This step's section header should not be similar to "Access the Web User Interface".
        2. Customize the article to apply to the specific device(s) or product(s) involved. If the question is not applicable to the device, simply state that the configuration is not supported.
        3. Use steps section title to group steps logically by task.
        4. Optionally use the 'note' key in each step to provide additional context about that step. Examples of notes: 'Configuring the SSH Settings for SCP is only applicable if the chosen downloaded protocols involves SCP.', 'The default username and password for the device is cisco/cisco.'
        5. Do not refer to the user or customer within the article.
    </rules>
    
    <context>
        {context}
    </context>
    """
    else:
        return """Role: You are a Cisco TAC Engineer with extensive technical knowledge about network switches, routers, access points, phones, and network management tools.
    
    Your task is to generate a step-by-step guide for configuring a specific feature on a Cisco device. Use the question as the configuration topic. Ensure the article tone is professional and technical. Personalize the article for the device mentioned in XML.
    
    Only use the context to generate the article. Ensure the article step text is written in Markdown format.
    
    <device>
        {device}
    </device>

    <question>
        {question}
    </question>
    
    <article-format>
        Title: Create a title based on the question '{question}' and context provided.
        
        Objective: Provide a concise objective in 1-2 sentences. Ensure to mention this configuration will be performed through the Command Line Interface. Use Markdown format for lists, bold, and italics
        
        Introduction: Write a 5-10 sentence introduction explaining the configuration, its features, and its benefits to the network. Use Markdown format for lists, bold, and italics.
        
        List of Steps:
            Each step should be a dictionary with the following keys:
                1. section: Describe what will be done in this group of steps.
                2. step_number: The step number within the section.
                3. text: Describe the action required to advance toward the objective. Write in Markdown format for lists, bold, code blocks, and italics.
                4. note (optional): Provide additional context, cautions, notes or common details often overlooked. Not required.
    </article-format>
    
    <rules>
        1. Every articles first step begins by logging into device Command Line Utility (CLI).
        2. Customize the article to apply to the specific device(s) or product(s) involved. If the question is not applicable to the device, simply state that the configuration is not supported.
        3. Use steps section title to group steps logically by task.
        4. Optionally use the 'note' key in each step to provide additional context about the step. Examples of notes: 'Configuring the SSH Settings for SCP is only applicable if the chosen downloaded protocols involves SCP.', 'The default username and password for the device is cisco/cisco.', 'In this example, Catalyst 1300 Switch is used.'
        5. Do not refer to the user or customer within the article.
        6. Articles WILL ALWAYS ASSUME THE USER IS IN GLOBAL CONFIGURATION MODE. THE USER ENTERS GLOBAL CONFIGURATION MODE BY ENTERING 'configure' on the Command Line. Example: '''configure''' , not '''configure terminal'''.
        7. Return from Global Configuration mode to Privileged EXEC mode by entering `exit`, `end`, or pressing `Ctrl+Z`.
        8. Upon a user entering Global Configuration mode, the prompt will consist of the device hostname followed by '(config)'. Example: 'CBS250(config)#'. Include this within the step text if applicable.
        9. Upon entering inteface configuration mode, the prompt will conist of the device hostname followed by '(config-if)'. Example: 'CBS250(config-if)#'. Include this within the step text if applicable.
    </rules>
        
        
    <context>
        {context}
    </context>
    """


def select_prompt_template(datasource: Literal["ADMIN_GUIDE", "CLI_GUIDE"]):
    """
    Selects the appropriate template given the datasource.

    Args:
        datasource (Literal[&quot;ADMIN_GUIDE&quot;, &quot;CLI_GUIDE&quot;]): The preferred method of enacting a device configuration given by the user.

    Returns:
        str: The prompt template to use.
    """
    if datasource == "ADMIN_GUIDE":
        return """Role: You are a Cisco TAC Engineer with extensive technical knowledge about network switches, routers, access points, phones, and network management tools.
    
    Your task is to generate a step-by-step guide for configuring a specific feature on a Cisco device. Use the question as the configuration topic. Personalize the article for the device mentioned in XML.
    
    Only use the context to generate the article. Ensure the article step text is written in Markdown format.
          
    <device>
        {device}
    </device>
    
    <question>
        {question}
    </question>
    
    <article-format>
        Title: Create a title based on the question '{question}' and context provided.
        
        Objective: Provide a concise objective in 1-2 sentences. Ensure to mention this configuration will be performed through the Web-Based Utility.
        
        Introduction: Write an introduction explaining the configuration, its features, and its benefits. 5-10 sentences. Use Markdown format for lists, bold, and italics.
        
        List of Steps:
            Each step should be a dictionary with the following keys:
                1. section: Describe what will be done in this group of related steps.
                2. step_number: The step number within the section. Step numbers start at 1 and increment by 1.
                3. text: Describe the action required to advance toward completing the objective. Write in Markdown format.
                4. note (optional): Provide additional context, cautions, notes or common details often overlooked. Examples could be supported cable types, default settings, or common mistakes.
    </article-format>
    
    
    <rules>
        1. The first step should always be "Log in to the web user interface (UI) of your switch".
        2. Customize the article to apply to the specific device(s) or product(s) involved. If the question is not applicable to the device, simply state that the configuration is not supported.
        3. Use steps section title to group steps logically by task.
        4. Optionally use the 'note' key in each step to provide additional context about that step. Examples of notes: 'Configuring the SSH Settings for SCP is only applicable if the chosen downloaded protocols involves SCP.', 'The default username and password for the device is cisco/cisco.', 'In this example, Catalyst 1300 Switch is used.'
        5. Do not refer to the user or customer within the article.
    </rules>
    
    <context>
        {context}
    </context>
    """
    else:
        return """Role: You are a Cisco TAC Engineer with extensive technical knowledge about network switches, routers, access points, phones, and network management tools.
    
    Your task is to generate a step-by-step guide for configuring a specific feature on a Cisco device. Use the question as the configuration topic. Ensure the article tone is professional and technical. Personalize the article for the device mentioned in XML.
    
    Only use the context to generate the article. Ensure the article step text is written in Markdown format.
    
    <device>
        {device}
    </device>

    <question>
        {question}
    </question>
    
    <article-format>
        Title: Create a title based on the question '{question}' and context provided.
        
        Objective: Provide a concise objective in 1-2 sentences. Ensure to mention this configuration will be performed through the Command Line Interface. Use Markdown format for lists, bold, and italics
        
        Introduction: Write a 5-10 sentence introduction explaining the configuration, its features, and its benefits to the network. Use Markdown format for lists, bold, and italics.
        
        List of Steps:
            Each step should be a dictionary with the following keys:
                1. section: Describe what will be done in this group of steps.
                2. step_number: The step number within the section.
                3. text: Describe the action required to advance toward the objective. Write in Markdown format for lists, bold, code blocks, and italics.
                4. note (optional): Provide additional context, cautions, notes or common details often overlooked. Not required.
    </article-format>
    
    <rules>
        1. Every articles first step begins by logging into device Command Line Utility (CLI).
        2. Customize the article to apply to the specific device(s) or product(s) involved. If the question is not applicable to the device, simply state that the configuration is not supported.
        3. Use steps section title to group steps logically by task.
        4. Optionally use the 'note' key in each step to provide additional context about the step. Examples of notes: 'Configuring the SSH Settings for SCP is only applicable if the chosen downloaded protocols involves SCP.', 'The default username and password for the device is cisco/cisco.', 'In this example, Catalyst 1300 Switch is used.'
        5. Do not refer to the user or customer within the article.
        6. Articles WILL ALWAYS ASSUME THE USER IS IN GLOBAL CONFIGURATION MODE. THE USER ENTERS GLOBAL CONFIGURATION MODE BY ENTERING 'configure' on the Command Line. Example: '''configure''' , not '''configure terminal'''.
        7. Return from Global Configuration mode to Privileged EXEC mode by entering `exit`, `end`, or pressing `Ctrl+Z`.
        8. Upon a user entering Global Configuration mode, the prompt will consist of the device hostname followed by '(config)'. Example: 'CBS250(config)#'. Include this within the step text if applicable.
        9. Upon entering inteface configuration mode, the prompt will conist of the device hostname followed by '(config-if)'. Example: 'CBS250(config-if)#'. Include this within the step text if applicable.
    </rules>
        
        
    <context>
        {context}
    </context>
    """


def identify_category(title: str):
    """
    Identify the category of the article.
    Args:
        title (str): The title of the created article.
    Returns:
        str: The category of the article.
    """

    def format_categories_list(categories: List[str]) -> str:
        return "\n".join(
            [f"{i + 1}. {category}" for i, category in enumerate(categories)]
        )

    categories = [
        "Configuration",
        "Install & Upgrade",
        "Troubleshooting",
        "Maintain & Operate",
        "Design",
    ]
    template = """Based on the given title, choose a category from categories that best fits the article. Follow the rules strictly.
    
    <rules>
        1. If the article is about troubleshooting a problem, choose the 'Troubleshooting' category.
        2. If the article title is about configuring a feature, choose the 'Configuration' category.
        3. If the article title is about upgrading or installing firmware or Day Zero setups, choose the 'Install & Upgrade' category.
        4. If the article is an overview of a feature or a best practice guide, choose the 'Maintain & Operate' category.
        5. If the article is about designing a network, a feature, or general guidance to newcomers then choose 'Design'.
        6. Most of our articles fall under the "Configuration" category but do not let this rule limit your choice. Choose the category that best fits the article.
    </rules>
    

    <categories>
        {categories}
    </categories>    
    
    
    <title>
        {title}
    </title>
    
    Return only the category name as a string and nothing else.
    """
    prompt = ChatPromptTemplate.from_template(template)
    model = setup_chat_openai()
    chain = prompt | model | StrOutputParser()
    category = chain.invoke(
        {"categories": format_categories_list(categories), "title": title}
    )
    return category


def add_article_metadata(state: GraphState):
    state_dict = state.get("keys")
    article = state_dict.get("article")[0].model_dump()
    category = "Configuration"
    revision_history = [
        {
            "revision": 1.0,
            "publish_date": datetime.now().strftime("%Y-%m-%d"),
            "comments": "Initial article creation.",
        }
    ]
    device = state_dict.get("device")
    applicable_devices = [{"device": device}]
    # temporary id for the frontend + routing purposes
    # a new ID will be generated by db, returned and set in activeArticle store
    id = str(uuid.uuid4())
    article.update(
        series=device,
        id=id,
        document_id=str(uuid.uuid4()),
        url=f"http://localhost:8080/article/{id}",
        category=category,
        applicable_devices=applicable_devices,
        revision_history=revision_history,
        created_at=int(time.time()),
        updated_at=int(time.time()),
    )
    # We need to construct this back to Pydantic Model without validation (allows for extra fields/metadatas)
    steps = [Step.model_construct(**step) for step in article.get("steps")]
    created_article = CreatedArticle.model_construct(**{**article, "steps": steps})
    state.get("keys").update({"article": [created_article]})
    return state


def determine_datasource(state: GraphState) -> str:
    """
    Determines what contextual information to retrieve based on the question.
    Returns either "ADMIN_GUIDE" or "CLI_GUIDE".
    Args:
        state (GraphState): The current state of the agent.
    Returns:
        str: Either "ADMIN_GUIDE" or "CLI_GUIDE".
    """
    state_dict = state.get("keys")
    question = state_dict.get("question")

    template = """You are a world class router. Using the question provided, determine which datasource to retrieve. You can only choose between: 'ADMIN_GUIDE' or 'CLI_GUIDE'.
    
    Return 'CLI_GUIDE' only if specifically referenced in the question.
    
    Some examples of being referenced are these forms within the question:
    
    1. Command Line Interface
    2. CLI
    3. Command Line
    4. Terminal
    
    Otherwise, return 'ADMIN_GUIDE'.
    
    Question: {question}
    """
    prompt = ChatPromptTemplate.from_template(template)
    model = setup_chat_openai().bind_tools(
        tools=[DataSourceType],
        tool_choice={"type": "function", "function": {"name": "DataSourceType"}},
    )
    chain = prompt | model | PydanticToolsParser(tools=[DataSourceType])
    answer = chain.invoke({"question": question})
    print(f"Type is: {answer}")
    datasource = answer[0].datasource if isinstance(answer, list) else answer
    state["keys"].update({"datasource": datasource})
    return state


def retrieve(state: GraphState) -> GraphState:
    """
    Retrieve documents
    Args:
        state (Dict): The current state of the agent.
    Returns:
        Dict: New key added to state, documents, that contain documents.
    """
    print("------RETRIEVE------")
    state_dict = state.get("keys")
    question = state_dict.get("question")
    datasource = state_dict.get("datasource")
    device_name = state_dict.get("device", "Cisco Catalyst 1200 Series Switches")

    if datasource == "ADMIN_GUIDE":
        collection_name = CollectionFactory.get_admin_guide_collection(device_name)
        retriever = init_parent_document_retriever(collection_name)
    else:
        collection_name = CollectionFactory.get_cli_guide_collection(device_name)
        vectordb = create_or_retrieve_db(collection_name=collection_name)
        llm = ChatOpenAI(temperature=0, model="gpt-4o")
        document_contents = "Command Line Interface commands, guidelines, syntax, description, parameters, and examples"
        retriever = init_self_query_retriever(
            llm, vectordb, document_contents, collection_name
        )

    subtopics, extended_documents = decompose_question(question, retriever)
    documents = search_vector_db([question], retriever)
    test_documents = query_doc_with_hybrid_search(
        collection_name=collection_name, query=question
    )
    documents.extend(extended_documents + test_documents)
    # filter out documents with same metadata doc_id
    filtered_docs = list({doc.metadata["doc_id"]: doc for doc in documents}.values())
    state["keys"].update({"documents": filtered_docs, "subtopics": subtopics})
    return state


def grade_documents(state: GraphState):
    state_dict = state.get("keys")
    documents = state_dict.get("documents", [])
    question = state_dict.get("question")
    subtopics = state_dict.get("subtopics", [])

    model = setup_chat_openai()
    grade_tool = convert_to_openai_tool(Grader)
    llm_with_tool = model.bind(
        tools=[convert_to_openai_tool(grade_tool)],
        tool_choice={"type": "function", "function": {"name": "Grader"}},
    )
    parser = PydanticToolsParser(tools=[Grader])
    template = """You are a grader assessing relevance of a retrieved document to a user's question and a set of possible subtopics derived from the question. The data will be supplied using XML Style Tags.
    
    <document>
        {context}
    </document>
    
    
    <question>
        {question}
    </question>
    
    <subtopics>
        {subtopics}
    </subtopics>
    
    
    If the documents contains keyword(s) or semantic meaning related to the user question and/or subtopics, grade it as 'yes' (relevant).
    Give a binary score of 'yes' or 'no' to indicate whether the document is relevant to the user question.
    
    """
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm_with_tool | parser
    filtered_docs = []
    for doc in documents:
        score = chain.invoke(
            {
                "context": doc.page_content,
                "question": question,
                "subtopics": ", ".join(subtopics),
            }
        )
        grade = score[0].binary_score if isinstance(score, list) else score.binary_score
        if grade == "yes":
            logger.info(f"Document: {doc} is relevant.")
            filtered_docs.append(doc)
    state["keys"].update({"documents": filtered_docs})
    return state


def generate_article_with_context(state: GraphState):
    """
    Generate the article using the context only.
    Args:
        state (Dict): The current state of the agent.
    Returns:
        Dict: New key added to state, `article`, that contains the generated article.
    """
    print("------GENERATE WITH CONTEXT------")
    state_dict = state.get("keys")
    documents = state_dict.get("documents", [])
    question = state_dict.get("question")
    device = state_dict.get("device")
    datasource = state_dict.get("datasource")
    subtopics = state_dict.get("subtopics", [])
    # template = select_prompt_template(datasource)
    template = test_prompt_template(datasource)

    tools = [CreatedArticle]
    prompt = ChatPromptTemplate.from_template(template)
    model = setup_chat_openai().bind_tools(
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "CreatedArticle"}},
    )
    chain = prompt | model | PydanticToolsParser(tools=[CreatedArticle])
    article = chain.invoke(
        {
            "context": format_docs(documents),
            "question": question,
            "device": device,
            "subtopics": ", ".join(subtopics),
        }
    )
    state["keys"].update({"article": article})
    return state


def generate_article_with_example(state: GraphState):
    """
    Polish the article now using the example
    Args:
        state (GraphState): The current state of the agent.
    """
    print("------GENERATE WITH EXAMPLE------")
    state_dict = state.get("keys")
    question = state_dict.get("question")
    article = state_dict.get("article")[0].model_dump()
    documents = state_dict.get("documents", [])
    videos_pipeline = [
        {
            "$search": {
                "index": "videos_search_index",
                "text": {
                    "query": f"{question}",
                    "path": {"wildcard": "*"},
                },
            }
        },
        {
            "$project": {
                "_id": 0,
                "title": 1,
                "transcript": 1,
            }
        },
        {"$limit": 2},
    ]
    example_videos = db_aggregate("videos", videos_pipeline)
    example_videos = [
        f"\nTitle: {video['title']}\n\nTranscript: {video['transcript']}"
        for video in example_videos
    ]

    system_message = """You are a TAC Engineer at Cisco who has supreme knowledge with configuring network switches, routers, wireless access points, phones and network management tools.
    You will be given the question, current-article state and context within XML-Style tags. Your task is to refine the <current-article> by ensuring it follows the correct format, improving clarity, and adding detailed explanations. Use the context to help guide you in both formatting and the steps to take to complete the configuration.
    Pay special attention to the specific device mentioned in the question.
    
    Rules To Follow:
        1. Every Article initial step begins either by logging into the device's Web-Based Utility or the Command Line Interface, if applicable.
        2. The objective states clearly the task of the article and mentions the configuration is either performed through the Web-Based Utility or Command Line Interface.
        3. The intoduction should explain the topic, discuss the importance of the configuration, and describe how the feature works in some detail.
        4. Customize the article to apply to the specific device(s) or product(s) involved.
        5. Use section header to group steps logically.
        6. Optionally use the 'note' key in each step to provide additional context about the step. Examples of notes: 'Configuring the SSH Settings for SCP is only applicable if the chosen downloaded protocols involves SCP.', 'The default username and password for the device is cisco/cisco.', 'In this example, Catalyst 1300 Switch is used.'
        7. Do not refer to the user or customer within the article.
        8. Break down complex steps into smaller, more manageable steps.
        9. If a feature is enabled or disabled by default, mention it in the 'note' key.
        10. Use the EXAMPLE ARTICLE to guide the format and structure of the CURRENT ARTICLE.
        11. Lightly explain any technical terms or concepts within the steps.
        12. Clarify any unclear steps by providing additional information.
        13. For CLI instructions, ensure the user is in global configuration mode by including the `configure` command.  
    """
    human_message = """Using the example-article to guide you, improve the current-article by adding detail and clarity. Focus on the specific device mentioned in the question. Use the context provided to enhance the article if applicable.
    
    <question>
        {question}
    </question>
    
    
    <current-article>
        {article}
    </current-article>
    
    
    
    <context>
        {context}
    </context>
    
    """
    prompt = ChatPromptTemplate.from_messages(
        [("system", system_message), ("human", human_message)]
    )
    tools = [CreatedArticle]

    model = setup_chat_openai().bind_tools(
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "CreatedArticle"}},
    )

    chain = prompt | model | PydanticToolsParser(tools=[CreatedArticle])
    new_article = chain.invoke(
        {
            "question": question,
            "article": article,
            "context": f"{format_docs(documents)}",
        }
    )
    state["keys"].update({"article": new_article})
    return state


def refine_article_steps(state: GraphState):
    state_dict = state["keys"]
    article = state_dict["article"][0].model_dump()

    template = """
    You are an AI copy editor with a keen eye for detail and a deep understanding of language, style, and grammar. Use the information provided within XML-Style tags.
    Your task is to refine and reorganize the steps in the provided JSON List of Steps for an <article>. You can think of the list of steps as a list of smaller tasks the user must complete to enact the desired configuration.
    Follow the <guidelines> below.
    Use the <examples> below that shows the <original> set of steps and the expected <result> results after refining the steps.

    <guidelines>
        1. Carefully review the entire JSON List of Steps, focusing on both the 'section' and 'text' of each step.

        2. Create logical groupings of steps and assign appropriate section headers. Develop new, concise section values that accurately describe each group of related steps.
           Steps within the same logical group should share the same section value.
           When the step content no longer fits the current section, create a new section header for the next group of steps.

        3. Handle login steps. Do not create a separate section for logging into a web-based utility or CLI. The initial step is the first step towards completing the step section task. Under no circumstances should the Log-In step have it's own section. Ensure you make this step the first step in completing the sub-objective and give it the proper section title based on the subsequent steps.

           Example: If the first step section is similar to "Log in to the Web-Based Utility", edit the section header based on the subsequent actions within the next steps.

        4. Maintain the original order of steps. Do not change the sequence of steps provided in the JSON List. Only re-name the sections by grouped sub-objectives.

        5. Use context from the entire Article JSON. While your primary focus is on refining the steps, use other information in the Article JSON to inform your decisions about logically grouping a set of related steps.

        6. Ensure clarity and coherence. Each step should clearly contribute to the overall objective of the article. Section titles should provide a clear overview of the steps they encompass.
    </guidelines>

    <examples>
        <original>
            steps:
              - section: "Log in to the Web-Based Utility"
                step_number: 1
                text: "Open a web browser and enter the IP address of your Cisco Business 350 Managed Switch. Log in using your administrator credentials."
                note: "The default username and password for the device is cisco/cisco."
              - section: "Navigate to DHCP Auto Update Settings"
                step_number: 1
                text: "Click on 'Administration' in the main menu, then select 'File Management' and click on 'DHCP Auto Update'."
                note: "For the Cisco Business 250 and 350 series, switch to Advanced mode by choosing Advanced from the drop-down list."
              - section: "Enable Auto Configuration via DHCP"
                step_number: 1
                text: "Check the box to enable 'Auto Configuration Via DHCP'."
                note: "Auto Configuration Via DHCP is enabled by default."
              - section: "Select Download Protocol for Auto Configuration"
                step_number: 1
                text: "Choose the download protocol from the following options: 'Auto By File Extension', 'TFTP Only', or 'SCP Only'."
                note: "The default option is 'Auto By File Extension', which uses SCP for files with the appropriate extension and TFTP for others."
        </original>
        
        <result>
            steps:
              - section: "Configure DHCP Auto Update"
                step_number: 1
                text: "Open a web browser and enter the IP address of your Cisco Business 350 Managed Switch. Log in using your administrator credentials."
                note: "The default username and password for the device is cisco/cisco."

              - section: "Configure DHCP Auto Update"
                step_number: 2
                text: "Click on 'Administration' in the main menu, then select 'File Management' and click on 'DHCP Auto Update'."
                note: "For the Cisco Business 250 and 350 series, switch to Advanced mode by choosing Advanced from the drop-down list."

              - section: "Configure DHCP Auto Update"
                step_number: 3
                text: "Check the box to enable 'Auto Configuration Via DHCP'."
                note: "Auto Configuration Via DHCP is enabled by default."

              - section: "Configure DHCP Auto Update"
                step_number: 4
                text: "Choose the download protocol from the following options: 'Auto By File Extension', 'TFTP Only', or 'SCP Only'."
                note: "The default option is 'Auto By File Extension', which uses SCP for files with the appropriate extension and TFTP for others."
        </result>
    </examples>

    Please refine the sections within the JSON list of steps with updated section values and step numbers, maintaining the original step order and overall structure of the article.
    Return the entire Article.
    
    <article>
        {article}
    </article>
    
    """
    prompt = ChatPromptTemplate.from_template(template)
    model = setup_chat_openai().bind_tools(
        tools=[CreatedArticle],
        tool_choice={"type": "function", "function": {"name": "CreatedArticle"}},
    )
    chain = prompt | model | PydanticToolsParser(tools=[CreatedArticle])
    refined_article = chain.invoke({"article": article})
    state["keys"].update({"article": refined_article})
    return state


def renumber_article_steps(state: GraphState):
    """
    Renumber the steps in the article. If the section value changes from the previous values, the step number should reset to 1.

    Args:
        state (GraphState): The current state of the agent.

    Returns:
        state: The final state of the agent.
    """
    article = state.get("keys").get("article")[0].model_dump()
    steps = article.get("steps")

    template = """You are an AI Assistant Editor. Use the information between XML-Style Tags. Renumber the steps in the list of steps for the article following the rules below.
    
    <rules>
        1. The first step in each section should be numbered 1.
        2. If the header section value changes from the previous section value, the step number should reset to 1.
        3. The step number should increment by 1 for each subsequent step within the same section.
        4. Do not change the section values or the order of the steps, only renumber the step_number.
    </rules>
    
    <steps>
        {steps}
    </steps>
    """
    prompt = ChatPromptTemplate.from_template(template)
    model = setup_chat_openai().bind_tools(
        tools=[Steps], tool_choice={"type": "function", "function": {"name": "Steps"}}
    )
    chain = prompt | model | PydanticToolsParser(tools=[Steps])
    renumbered_steps = chain.invoke({"steps": steps})
    modelled_steps = (
        renumbered_steps[0].steps
        if isinstance(renumbered_steps, list)
        else renumbered_steps.steps
    )
    validated_steps = [
        Step.model_validate(step.model_dump()) for step in modelled_steps
    ]
    created_article = CreatedArticle.model_construct(
        **{**article, "steps": validated_steps}
    )
    state.get("keys").update({"article": [created_article]})
    return state


def convert_markdown_to_html(text: str) -> str:
    html = markdown.markdown(text)
    logger.debug(f"Converted markdown to HTML: {html}")
    return html


def build_html_for_admin_guide_sources(state: GraphState):
    """
    Convert the article to HTML.

    Args:
        state (GraphState): The current state of the agent.

    Returns:
        state: The final state of the agent.
    """
    state_dict = state["keys"]
    article = state_dict.get("article")[0].model_dump()
    article_intro = convert_markdown_to_html(article["introduction"])
    article_steps = article["steps"]
    steps_html = ""
    for step in article_steps:
        text = convert_markdown_to_html(step["text"])
        note = step.get("note", None)
        if step["step_number"] == 1:
            steps_html += f"""
            <div class="cdt-step">
                <h4>{step['section']}</h4>
                <h5>Step {step['step_number']}</h5>
                <p>{text}</p>
                {f'<div class="cdt-note">{note}</div>' if note else ''}
            </div>
            """
        else:
            steps_html += f"""
            <div class="cdt-step">
                <h5>Step {step['step_number']}</h5>
                <p>{text}</p>
                {f'<div class="cdt-note">{note}</div>' if note else ''}
            </div>
            """
    combined_html = f"""
    <!DOCTYPE html>
    <html lang='en'>
        <head>
            <meta charset='UTF-8'>
            <meta name='viewport' content='width=device-width, initial-scale=1.0'>
            <title>{article['title']}</title>
            <meta name="description" content="{article['objective']}">
            <meta name="title" content="{article['title']}">
            <link rel='stylesheet' href='../css/articles.css'>
        </head>
        <body>
        <div class="container">
            <h1>{article['title']}</h1>
            <div class="links-container">
                <div class="links_row">
                        <div class="toolbar">
                            <div class="save" id="saveModule">
                                <button style="display: flex; align-items: center;" class="save">
                                    <ion-icon style="color: var(--cisco-dark-gray);" name="save"></ion-icon>
                                    <span style="display: block;">Save</span>
                                </button>
                            </div>
                            <div class="download">
                                <button style="display: flex; align-items: center;" class="download">
                                    <ion-icon style="color: var(--cisco-dark-gray);" name="download"></ion-icon>
                                    <span style="display: block;">Download</span>
                                </button>
                            </div>
                        </div>
                    </div>
                    <div class="info-bar">
                        <div class="publish-date">
                            <span>Published on: </span>
                            <time>{article['revision_history'][0]['publish_date']}</time>
                        </div>
                        <div class="doc-id">
                            <span>Document ID: </span>
                            <p>{article['document_id']}</p>
                        </div>
                    </div>
                </div>
                <div id="eot-doc-wrapper">
                    <h2>Objective</h2>
                    <p>{article['objective']}</p>
                    <h3>Introduction</h3>
                    {article_intro}
                    {steps_html}
                </div>
            </div>
            <script type="module" src="https://unpkg.com/ionicons@7.1.0/dist/ionicons/ionicons.esm.js"></script>
            <script src="../js/formats.js"></script>
        </div>
        </body>
    </html>
    """
    state["keys"].update({"html": combined_html})
    return state


def add_html_formatting(html: str, article: dict):
    revision_history = article["revision_history"][0]
    publish_date = revision_history["publish_date"]
    doc_id = article["document_id"]
    return f"""
    <!DOCTYPE html>
    <html lang='en'>
        <head>
            <meta charset='UTF-8'>
            <meta name='viewport' content='width=device-width, initial-scale=1.0'>
            <title>{article['title']}</title>
            <link rel='stylesheet' href='../css/articles.css'>
        </head>
        <body>
        <div class="container">
            <div class="links_row">
                <div class="toolbar">
                    <div class="save" id="saveModule">
                        <button class="save">
                            <ion-icon style="color: var(--cisco-dark-gray);" name="save"></ion-icon>
                            <span style="display: block;">Save</span>
                        </button>
                    </div>
                    <div class="download">
                        <button class="download">
                            <ion-icon style="color: var(--cisco-dark-gray);" name="download"></ion-icon>
                            <span style="display: block;">Download</span>
                        </button>
                    </div>
                </div>
            </div>
            <div class="info-bar">
                <div class="publish-date">
                    <span>Published on: </span>
                    <time>{publish_date}</time>
                </div>
                <div class="doc-id">
                    <span>Document ID: </span>
                    <p>{doc_id}</p>
                </div>
            </div>
            {html}
            <script type="module" src="https://unpkg.com/ionicons@7.1.0/dist/ionicons/ionicons.esm.js"></script>
            <script nomodule src="https://unpkg.com/ionicons@7.1.0/dist/ionicons/ionicons.js"></script>
            <script src="../js/formats.js"></script>
        </div>
        </body>
    </html>
    """


def build_html_for_cli_guide_sources(state: GraphState):
    """
    Output the final article to valid Markdown for frontend.
    Args:
        state (GraphState): The current state of the agent.
    Returns:
        Dict: The final state of the agent.
    """
    model = setup_chat_openai()
    template = """You are a Senior Frontend Developer. You have been tasked with taking an article and converting its components into valid HTML for the front-end.
        Following the rules below, convert the article into valid HTML.

        <rules>
            1. Evaluate each component of the article. Determine if the text is better presented in a simple paragragh, an ordered list, an unordered list, or other semantic element.
            2. Write 'Objective' with an h2 element and put the associated text inside a paragraph below that.
            3. Write 'Introduction' with an h3 element. Put the introduction text inside paragraphs or unordered-list elements below the h3, if applicable.
            4. Iterate each step in the steps list.
            5. Wrap each step within a section element with a class name of "cdt-step".
            6. If the step_number is 1, write the section value with an h4 element. If the step_number is greater than 1, omit the section value.
            7. With an h5 element, write `Step ` and the step_number. Example: `Step 2`. Put the step text inside a paragraph element or unordered-list if displaying list items.
            8. If the step has a note, write the note text below the step text. Use a div element with a class name of "cdt-note" to wrap the note text.
            9. Wrap CLI commands within <kbd> and <code> elements. The <kbd> element should have the class "kbd-cdt cCN_CmdName" and the data-label "click to copy command". The <code> element should have the class "code-cdt".
            10. Wrap the entire article within a div element with an id of "eot-doc-wrapper".
        </rules>
        
        Following the rules above, convert this article into valid HTML. Return as a string. Only return #eot-doc-wrapper and its children.
        
        <article>
            {article}
        </article>
    """
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | model | StrOutputParser()
    state_dict = state["keys"]
    article = state_dict.get("article")[0].model_dump()
    html = chain.invoke({"article": article})
    html5 = add_html_formatting(html, article)
    state["keys"].update({"html": html5})
    return state


def decide_html_build_path(state: GraphState):
    state_dict = state["keys"]
    datasource = state_dict["datasource"]

    if datasource == "ADMIN_GUIDE":
        return "build_html_for_admin_guide_sources"
    else:
        return "build_html_for_cli_guide_sources"


workflow = StateGraph(GraphState)

workflow.add_node("determine_datasource", determine_datasource)
workflow.add_node("retrieve", retrieve)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("generate_article_with_context", generate_article_with_context)
workflow.add_node("refine_article_steps", refine_article_steps)
workflow.add_node("renumber_article_steps", renumber_article_steps)
workflow.add_node("add_article_metadata", add_article_metadata)

workflow.set_entry_point("determine_datasource")
workflow.add_edge("determine_datasource", "retrieve")
workflow.add_edge("retrieve", "grade_documents")
workflow.add_edge("grade_documents", "generate_article_with_context")
workflow.add_edge("generate_article_with_context", "refine_article_steps")
workflow.add_edge("refine_article_steps", "renumber_article_steps")
workflow.add_edge("renumber_article_steps", "add_article_metadata")
workflow.add_edge("add_article_metadata", END)


from langchain_core.runnables import RunnableConfig

ARTICLE_GRAPH = workflow.compile()


async def build_article(question: str, device: str):

    inputs: dict[str, GraphState] = {"keys": {"question": question, "device": device}}
    article = {}
    sources = []
    html = None

    state: dict[str, GraphState] = await ARTICLE_GRAPH.ainvoke(inputs)
    if graph_state := state.get("keys"):
        documents = graph_state.get("documents", [])
        for doc in documents:
            sources.append(
                {
                    "id": doc.metadata.get("doc_id"),
                    "source": (
                        doc.metadata.get("source")
                        if doc.metadata.get("source", None)
                        else doc.metadata.get("url", None)
                    ),
                }
            )
    article = (
        state.get("keys").get("article")[0].model_dump()
        if isinstance(state.get("keys").get("article"), list)
        else state.get("keys").get("article").model_dump()
    )
    if len(sources) > 0:
        print(f"Sources: {sources}")
        article["sources"] = sources

    return article


# article = None
# html = None


def save(article, html):
    if article:
        with open(
            f"{BASE_DIR}/backend/data/cisco/{'_'.join(article['title'].lower().split())}.json",
            "w",
        ) as f:
            json.dump(article, f, indent=2)

    if html:
        with open(
            f"{BASE_DIR}/backend/data/cisco/html/{'_'.join(article['title'].lower().split())}.html",
            "w",
        ) as f:
            f.write(html)
