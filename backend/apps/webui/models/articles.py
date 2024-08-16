from langchain.pydantic_v1 import BaseModel, Field
from langchain.schema import Document
from typing import Optional, List, TypedDict, Literal, Any, Dict


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


class Article(BaseModel):
    """
    Article model.
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
