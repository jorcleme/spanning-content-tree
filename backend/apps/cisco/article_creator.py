import os
import uuid
import json
import pymongo
import pymongo.errors
import logging
import markdown
from datetime import datetime
from pymongo import MongoClient
from dotenv import load_dotenv, find_dotenv
from pprint import pprint
from typing import Dict, List, Any, Optional, Literal
from chromadb.api.types import GetResult
from apps.webui.models.articles import (
    CreatedArticle,
    DataSourceType,
    Search,
    GraphState,
    Grader,
)
from apps.cisco.examples import create_decomposition_search_examples

from apps.cisco.utils import (
    remove_props_from_dict,
    tool_example_to_messages_helper,
)
from apps.cisco.mongo_client import MongoDbClient
from config import (
    BASE_DIR,
    DATA_DIR,
    CHROMA_CLIENT,
    CATALYST_1300_ADMIN_GUIDE_COLLECTION_NAME,
    CATALYST_1300_CLI_GUIDE_COLLECTION_NAME,
    CATALYST_1200_ADMIN_GUIDE_COLLECTION_NAME,
    CATALYST_1200_CLI_GUIDE_COLLECTION_NAME,
    CBS_250_ADMIN_GUIDE_COLLECTION_NAME,
    CBS_250_CLI_GUIDE_COLLECTION_NAME,
)
from langchain.output_parsers.openai_tools import PydanticToolsParser
from langchain.storage.in_memory import InMemoryStore
from langchain.schema import Document
from langchain.retrievers.parent_document_retriever import ParentDocumentRetriever
from langchain.retrievers.multi_vector import SearchType
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.chains.query_constructor.base import AttributeInfo
from langchain_community.vectorstores.chroma import Chroma
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info(f"Logger name: {logger.name}")
logger.info(f"Logger level: {logger.level}")
logger.info(f"Module: {__name__}")

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


def get_llm(model: str = "gpt-4o", temperature: int = 0, verbose: bool = True):
    return ChatOpenAI(model=model, temperature=temperature, verbose=verbose)


def format_docs(documents: List[Document]) -> str:
    """
    Formats a list of documents into a single string with separators.

    Args:
        documents (List[Document]): A list of Document objects to format.

    Returns:
        str: A formatted string representation of the documents.
    """
    return f"\n{'-' * 100}\n".join(
        [f"Document {i+1}:\n\n" + doc.page_content for i, doc in enumerate(documents)]
    )


def format_other_sources(sources: List[str]) -> str:
    return f"\n{'-' * 100}\n".join(
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
        for doc, meta in zip(results["documents"], results["metadatas"])
    ]


def get_text_splitter():
    """
    Returns a configured RecursiveCharacterTextSplitter instance.

    Returns:
        RecursiveCharacterTextSplitter: Text splitter configured for chunking text.
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=300, chunk_overlap=0, add_start_index=True
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
        embedding_function=OpenAIEmbeddings(),
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


def init_parent_document_retriever(collection_name: str, vectordb: Chroma):
    """
    Initialize a parent document retriever for the given collection.

    Args:
        collection_name (str): The name of the collection to use.
        vectordb (Chroma): The vector database to use.

    Returns:
        ParentDocumentRetriever: The parent document retriever instance.
    """
    try:
        collection = CHROMA_CLIENT.get_collection(name=collection_name)
    except Exception as e:
        raise ValueError(f"Failed to get collection {collection_name}: {e}")

    docs = collection.get()
    print(len(docs["documents"]))
    ids = [doc["doc_id"] for doc in docs["metadatas"]]
    store = InMemoryStore()
    retriever = ParentDocumentRetriever(
        vectorstore=vectordb,
        docstore=store,
        id_key="doc_id",
        child_splitter=get_text_splitter(),
        search_kwargs={"k": 3},
        search_type=SearchType.similarity,
    )
    formatted_documents = convert_to_documents(docs)
    retriever.add_documents(documents=formatted_documents, ids=ids)

    # Smoketest to check large and small chunks
    # Retriever should return the large chunks
    # Vectorstore should return the small chunks
    large_chunks = retriever.invoke("Configure Bluetooth on Catalyst 1300")
    print(f"Large Chunks: {len(large_chunks[0].page_content)}")
    small_chunks = retriever.vectorstore.similarity_search(
        "Configure Bluetooth on Catalyst 1300"
    )
    print(f"Small Chunks: {len(small_chunks[0].page_content)}")
    print("Store Length of Keys " + str(len(list(store.yield_keys()))))
    print(f"Chroma DB Documents {len(docs['documents'])}")
    # Print the length of documents in the vectorstore
    print("Length of Formatted Docs" + str(len(formatted_documents)))
    return retriever


def decompose_question(question: str, retriever: BaseRetriever) -> List[Document]:
    examples = create_decomposition_search_examples()
    example_messages = [
        msg for ex in examples for msg in tool_example_to_messages_helper(ex)
    ]
    system = """
        You are an expert at converting user question into database queries. You have access to a database of documents that contain information about configuring a Cisco Switch, Cisco Router, or Cisco Wireless Access Point.
        
        Perform query decomposition. Given a user question, break it down into subtopics which will help answer questions related to the main topic.
        Each subtopic should be about a single concept/fact/idea. The subtopic should be other configurations, commands, or settings that are related to the main topic.
        
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
        | get_llm().with_structured_output(Search)
    )
    answer = query_analyzer.invoke(question)
    expanded_questions = [query for query in answer.subtopics]
    expanded_questions.append(question)  # Add the original question
    print(f"Queries: {expanded_questions}")
    documents = []
    for query in expanded_questions:
        documents.extend(retriever.invoke(query))
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

    Task: Write an article that guides a user through setting a configuration on their device based on the question below. Follow the article format and rules strictly.
          Use only the context below as your knowledge base.

    <question>
        {question}
    </question>
    
    <article-format>
        Title: Create a title based on the question '{question}' and context provided.
        
        Objective: Provide a concise objective in 1-2 sentences. Ensure to mention this configuration will be performed through the Web-Based Utility.
        
        Introduction: Write an introduction explaining the configuration, its features, and its benefits. 5-10 sentences.
        
        List of Steps:
            Each step should be a dictionary with the following keys:
                1. section: Header that describes the task of this group of steps.
                2. step_number: The step number within the section.
                3. text: Describe the action required to advance toward completing the objective.
                4. note (optional): Provide additional context, cautions, notes or common details often overlooked.
    </article-format>
    
    
    <rules>
        1. The first step should always be "Log in to the web user interface (UI) of your switch".
        2. Customize the article to apply to the specific device(s) or product(s) involved. If the question is not applicable to the device, simply state that the configuration is not supported.
        3. Use steps section title to group steps logically by task.
        4. If the section header changes, the steps start back at 1.
        5. Optionally use the 'note' key in each step to provide additional context about that step. Examples of notes: 'Configuring the SSH Settings for SCP is only applicable if the chosen downloaded protocols involves SCP.', 'The default username and password for the device is cisco/cisco.', 'In this example, Catalyst 1300 Switch is used.'
        6. Do not refer to the user or customer within the article.
    </rules>
    
    <context>
        {context}
    </context>
    """
    else:
        return """Role: You are a Cisco TAC Engineer with extensive technical knowledge about network switches, routers, access points, phones, and network management tools.

    Task: Write an article that guides a user through setting a configuration on their device based on the question below. Follow the article format and rules strictly.
          Use the context below to assist you in writing the article.

    <question>
        {question}
    </question>
    
    <article-format>
        Title: Create a title based on the question '{question}' and context provided.
        
        Objective: Provide a concise objective in 1-2 sentences. Ensure to mention this configuration will be performed through the Command Line Interface.
        
        Introduction: Write a 5-10 sentence introduction explaining the configuration, its features, and its benefits to the network.
        
        List of Steps:
            Each step should be a dictionary with the following keys:
                1. section: Describe what will be done in this group of steps.
                2. step_number: The step number within the section.
                3. text: Describe the action required to advance toward the objective.
                4. note (optional): Provide additional context, cautions, notes or common details often overlooked.
    </article-format>
    
    <rules>
        1. Every articles first step begins by logging into device Command Line Utility (CLI).
        2. Customize the article to apply to the specific device(s) or product(s) involved. If the question is not applicable to the device, simply state that the configuration is not supported.
        3. Use steps section title to group steps logically by task.
        4. If a steps section header changes, the steps start back at 1.
        5. Optionally use the 'note' key in each step to provide additional context about the step. Examples of notes: 'Configuring the SSH Settings for SCP is only applicable if the chosen downloaded protocols involves SCP.', 'The default username and password for the device is cisco/cisco.', 'In this example, Catalyst 1300 Switch is used.'
        6. Do not refer to the user or customer within the article.
        7. Articles WILL ALWAYS ASSUME THE USER IS IN GLOBAL CONFIGURATION MODE. THE USER ENTERS GLOBAL CONFIGURATION MODE BY ENTERING 'configure' on the Command Line. Just 'configure' unless otherwise specified.
        8. Return from Global Configuration mode to Privileged EXEC mode by entering `exit`, `end`, or pressing `Ctrl+Z`.
        9. Upon a user entering Global Configuration mode, the prompt will consist of the device hostname followed by '(config)'. Example: 'CBS250(config)#'. Include this within the step if applicable.
        10. Upon entering inteface configuration mode, the prompt will conist of the device hostname followed by '(config-if)'. Example: 'CBS250(config-if)#'. Include this within the step if applicable.
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
    model = get_llm()
    chain = prompt | model | StrOutputParser()
    category = chain.invoke(
        {"categories": format_categories_list(categories), "title": title}
    )
    return category


def add_article_metadata(state: GraphState):
    state_dict = state["keys"]
    article = state_dict["article"][0].dict()
    article["document_id"] = str(uuid.uuid4())
    revision_history = []
    revision = {
        "revision": 1.0,
        "publish_date": datetime.now().strftime("%Y-%m-%d"),
        "comments": "Initial article creation.",
    }
    revision_history.append(revision)
    article["revision_history"] = revision_history
    # We need to construct this back to Pydantic Model without validation
    article = CreatedArticle.construct(**article)
    state["keys"].update({"article": [article]})
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
    state_dict = state["keys"]
    question = state_dict["question"]

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
    model = get_llm().bind_tools(
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
    state_dict = state["keys"]
    question = state_dict["question"]
    datasource = state_dict["datasource"]

    if datasource == "ADMIN_GUIDE":
        vectordb = create_or_retrieve_db(CATALYST_1200_ADMIN_GUIDE_COLLECTION_NAME)
        retriever = init_parent_document_retriever(
            CATALYST_1200_ADMIN_GUIDE_COLLECTION_NAME, vectordb
        )
    else:
        vectordb = create_or_retrieve_db(CATALYST_1200_CLI_GUIDE_COLLECTION_NAME)
        llm = ChatOpenAI(temperature=0, model="gpt-4o")
        document_contents = "Command Line Interface commands, guidelines, syntax, description, parameters, and examples"
        retriever = init_self_query_retriever(
            llm, vectordb, document_contents, CATALYST_1200_CLI_GUIDE_COLLECTION_NAME
        )

    documents = decompose_question(question, retriever)
    # filter out documents with same metadata doc_id
    filtered_docs = list({doc.metadata["doc_id"]: doc for doc in documents}.values())
    state["keys"].update({"documents": filtered_docs})
    return state


def grade_documents(state: GraphState):
    state_dict = state["keys"]
    documents = state_dict["documents"]
    question = state_dict["question"]

    model = get_llm()
    grade_tool = convert_to_openai_tool(Grader)
    llm_with_tool = model.bind(
        tools=[convert_to_openai_tool(grade_tool)],
        tool_choice={"type": "function", "function": {"name": "Grader"}},
    )
    parser = PydanticToolsParser(tools=[Grader])
    template = """You are a grader assessing relevance of a retrieved document to a user's questions.
    
    Here is the retrieved document:
    
    {context}
    
    Here is the original user question:
    
    {question}
    
    If the documents contains keyword(s) or semantic meaning related to the user question, grade it as 'yes' (relevant).
    Give a binary score of 'yes' or 'no' to indicate whether the document is relevant to the user question.
    
    """
    prompt = ChatPromptTemplate.from_template(template)
    chain = prompt | llm_with_tool | parser
    filtered_docs = []
    for doc in documents:
        score = chain.invoke({"context": doc.page_content, "question": question})
        grade = score[0].binary_score if isinstance(score, list) else score.binary_score
        if grade == "yes":
            logger.info(f"Document: {doc.metadata['topic']} is relevant.")
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
    state_dict = state["keys"]
    documents = state_dict["documents"]
    question = state_dict["question"]
    datasource = state_dict["datasource"]
    template = select_prompt_template(datasource)

    tools = [CreatedArticle]
    prompt = ChatPromptTemplate.from_template(template)
    model = get_llm().bind_tools(
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "CreatedArticle"}},
    )
    chain = prompt | model | PydanticToolsParser(tools=[CreatedArticle])
    article = chain.invoke({"context": format_docs(documents), "question": question})
    state["keys"].update({"article": article})
    return state


def generate_article_with_example(state: GraphState):
    """
    Polish the article now using the example
    Args:
        state (GraphState): The current state of the agent.
    """
    print("------GENERATE WITH EXAMPLE------")
    state_dict = state["keys"]
    question = state_dict["question"]
    article = state_dict["article"][0].dict()
    example_articles = db_aggregate(
        "articles",
        [
            {
                "$search": {
                    "index": "articles_search_index",
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
                    "objective": 1,
                    "intro": 1,
                    "steps": 1,
                    "score": {"$meta": "searchScore"},
                }
            },
            {"$limit": 1},
        ],
    )
    results = []
    for a in example_articles:
        steps = list(
            map(
                lambda step: remove_props_from_dict(
                    step,
                    "emphasized_tags",
                    "emphasized_text",
                    "src",
                    "alt",
                    "video_src",
                ),
                a["steps"],
            )
        )
        steps = list(
            map(lambda step: {"step_number": step.pop("step_num"), **step}, steps)
        )
        a["steps"] = steps
        results.append(a)
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
    Your task is to refine the <current-article> by ensuring it follows the correct format, improving clarity, and adding detailed explanations. Use the <example-article> as a template to guide you in this process.
    Pay special attention to the specific device mentioned in the question.
    
    Rules To Follow:
        1. Every Article initial step begins either by logging into the device's Web-Based Utility or the Command Line Interface, if applicable.
        2. The objective must start with "The objective of this article is..." and mention the configuration is performed through the Web-Based Utility or Command Line Interface.
        3. The intoduction should explain the topic, discuss the importance of the configuration, and describe how the feature works in some detail.
        4. Customize the article to apply to the specific device(s) or product(s) involved.
        5. Use section header to group steps logically. When a section headers changes from the value of the previous steps, the step_number resets back to 1.
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
    
    
    
    <example-article>
        {example}
    </example-article>
    
    
    
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

    model = get_llm().bind_tools(
        tools=tools,
        tool_choice={"type": "function", "function": {"name": "CreatedArticle"}},
    )

    chain = prompt | model | PydanticToolsParser(tools=[CreatedArticle])
    new_article = chain.invoke(
        {
            "question": question,
            "example": results.pop(0),
            "article": article,
            "context": format_other_sources(example_videos),
        }
    )
    state["keys"].update({"article": new_article})
    return state


def refine_article_steps(state: GraphState):
    state_dict = state["keys"]
    article = state_dict["article"][0].dict()

    template = """
    You are an AI copy editor with a keen eye for detail and a deep understanding of language, style, and grammar.
    Your task is to refine and reorganize the steps in the provided JSON List of Steps for an <article>. You can think of the list of steps as a list of smaller tasks the user must complete to enact the desired configuration.
    Follow the <guidelines> below.
    Use the <examples> below that shows the <original> set of steps and the expected <edited> results after refining the steps.

    <guidelines>
        1. Carefully review the entire JSON List of Steps, focusing on both the 'section' and 'text' of each step.

        2. Create logical groupings of steps and assign appropriate section headers. Develop new, concise section values that accurately describe each group of related steps.
           Steps within the same logical group should share the same section value.
           When the step content no longer fits the current section, create a new section header for the next group of steps.

        3. Adjust step numbering. When a new section begins, reset the step_number to 1.
           Increment the step_number within each section until a new section starts.

        4. Handle login steps. Do not create a separate section for logging into a web-based utility or CLI. The initial step is the first step towards completing the step section task. Under no circumstances should the Log-In step have it's own section. Ensure you make this step the first step in completing the sub-objective and give it the proper section title based on the subsequent steps.

           Example: For "Configure DHCP Auto Update," make logging in the first step of this section.

        5. Maintain the original order of steps. Do not change the sequence of steps provided in the JSON List. Only re-name the sections by sub-objectives.

        6. Use context from the entire Article JSON. While your primary focus is on refining the steps, use other information in the Article JSON to inform your decisions about logically grouping a set of related steps.

        7. As a guide, an article typically only has 2-4 sub-objectives. There are special cases, however.

        8. Ensure clarity and coherence. Each step should clearly contribute to the overall objective of the article. Section titles should provide a clear overview of the steps they encompass.
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
        
        <edited>
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
        </edited>
    </examples>

    Please refine the sections within the JSON list of steps with updated section values and step numbers, maintaining the original step order and overall structure of the article.
    Return the entire Article.
    
    <article>
        {article}
    </article>
    
    """
    prompt = ChatPromptTemplate.from_template(template)
    model = get_llm().bind_tools(
        tools=[CreatedArticle],
        tool_choice={"type": "function", "function": {"name": "CreatedArticle"}},
    )
    chain = prompt | model | PydanticToolsParser(tools=[CreatedArticle])
    refined_article = chain.invoke({"article": article})
    state["keys"].update({"article": refined_article})
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
    article = state_dict["article"][0].dict()
    article_intro = convert_markdown_to_html(article["introduction"])
    article_steps = article["steps"]
    steps_html = ""
    for step in article_steps:
        text = step["text"]
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
    model = get_llm()
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
    article = state_dict["article"][0].dict()
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
workflow.add_node("generate_article_with_example", generate_article_with_example)
workflow.add_node("refine_article_steps", refine_article_steps)
workflow.add_node("add_article_metadata", add_article_metadata)
workflow.add_node(
    "build_html_for_admin_guide_sources", build_html_for_admin_guide_sources
)
workflow.add_node("build_html_for_cli_guide_sources", build_html_for_cli_guide_sources)
# workflow.add_node("article_to_html", article_to_html)

workflow.set_entry_point("determine_datasource")
workflow.add_edge("determine_datasource", "retrieve")
workflow.add_edge("retrieve", "generate_article_with_context")
workflow.add_edge("generate_article_with_context", "grade_documents")
workflow.add_edge("grade_documents", "generate_article_with_example")
workflow.add_edge("generate_article_with_example", "refine_article_steps")
workflow.add_edge("refine_article_steps", "add_article_metadata")
workflow.add_conditional_edges(
    "add_article_metadata",
    decide_html_build_path,
    {
        "build_html_for_admin_guide_sources": "build_html_for_admin_guide_sources",
        "build_html_for_cli_guide_sources": "build_html_for_cli_guide_sources",
    },
)
workflow.add_edge("build_html_for_admin_guide_sources", END)
# workflow.add_edge("refine_article_steps", "article_to_html")
workflow.add_edge("build_html_for_cli_guide_sources", END)


ARTICLE_GRAPH = workflow.compile()

question = (
    "Configure Advanced Voice Quality of Service (QoS) on a Cisco Catalyst 1200 Switch"
)

inputs: dict[str, GraphState] = {"keys": {"question": question}}

article = None
html = None


for output in ARTICLE_GRAPH.stream(inputs, stream_mode="updates"):
    for key, value in output.items():
        pprint(f"Output from node: {key}")
        pprint("--------------------")
        pprint(f"Value: {value}")
        print("\n")
        print("\n")
        if "article" in value["keys"]:
            if isinstance(value["keys"]["article"], list):
                article = value["keys"]["article"][0].dict()

            elif isinstance(value["keys"]["article"], dict):
                article = value["keys"]["article"]
        if "html" in value["keys"]:
            html = value["keys"]["html"]
    pprint("\n ------------------- \n")
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