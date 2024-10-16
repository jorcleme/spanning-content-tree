# Description: This module generates questions and answers for each step in a Cisco article.
# The questions are generated dynamically based on the previous steps and the answers are generated
# based on the context of the step, the generated question, and the context of the admin guide.
# The module also generates static answers based on 3 pre-defined questions.

# IMO, Generated Questions and Answers should be fetched from the front-end on demand by the user.
# This will benefit by reducing the amount of article creation time. Also, a user may never need all the questions and answers.
# Once a request is made to generate questions and answers, these questions should be stored in the database / cache and fetched on demand.

import json
from dotenv import find_dotenv, load_dotenv
from typing import (
    TypedDict,
    List,
    Optional,
    Literal,
    Any,
    Dict,
    ClassVar,
    TypeGuard,
    Annotated,
    Union,
)
from config import (
    CHROMA_CLIENT,
    CATALYST_1300_ADMIN_GUIDE_COLLECTION,
    CBS_220_ADMIN_GUIDE_COLLECTION,
)
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.schema import Document, StrOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain.retrievers.parent_document_retriever import ParentDocumentRetriever
from langchain_core.retrievers import BaseRetriever
from langchain_core.language_models import BaseLanguageModel
from langchain.prompts import PromptTemplate
from langchain.chains.combine_documents.refine import RefineDocumentsChain
from langchain.chains.llm import LLMChain
from langchain.storage import InMemoryStore
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


load_dotenv(find_dotenv(raise_error_if_not_found=True))


# Helper function - Removes dependency of PydanticOutputParser if desired
# Currently not being used
def extract_json(message: AIMessage) -> List[dict]:
    import re

    text = message.content
    pattern = r"```json(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    try:
        return [json.loads(match.strip()) for match in matches]
    except Exception:
        raise ValueError(f"Failed to parse: {message}")


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


def get_llm(model: str = "gpt-4o", temp: float = 0, verbose: bool = False):
    return ChatOpenAI(model=model, temperature=temp, verbose=verbose)


class Step(TypedDict, total=False):
    section: str
    step_number: int
    text: str
    note: Optional[str]


class Article(TypedDict, total=False):
    title: str
    objective: str
    introduction: str
    steps: List[Step]


ArticleKey = Annotated[str, "title", "objective", "introduction", "steps"]


class Question(BaseModel):
    """A single question a user might ask about the last step."""

    question: str = Field(
        ...,
        title="Question",
        description="A question that a user might ask about a step in the article.",
    )


class QuestionResponse(BaseModel):
    """A response containing a list of 3 questions a user might ask about the last step."""

    questions: List[Question] = Field(
        ...,
        title="Questions",
        description="A list of 3 questions that a user might ask about a step in the article.",
    )


class ParentRetriever:
    def __init__(self, collection_name: str):
        self.collection_name = collection_name

    def init_retriever(self) -> ParentDocumentRetriever:
        collection = CHROMA_CLIENT.get_or_create_collection(self.collection_name)
        results = collection.get()
        documents = [
            Document(page_content=doc, metadata=meta)
            for doc, meta in zip(results["documents"], results["metadatas"])
        ]
        vectorstore = Chroma(
            collection_name=f"{self.collection_name}_langchain",
            embedding_function=OpenAIEmbeddings(),
        )
        store = InMemoryStore()
        splitter = RecursiveCharacterTextSplitter(chunk_size=400, add_start_index=True)
        retriever = ParentDocumentRetriever(
            vectorstore=vectorstore, docstore=store, child_splitter=splitter
        )
        ids = [doc["doc_id"] for doc in results["metadatas"]]
        retriever.add_documents(documents, ids=ids)
        return retriever


from langchain.chains.combine_documents import create_stuff_documents_chain


class ReduceDocumentsChain:
    def __init__(self, prompt: Optional[PromptTemplate] = None):
        if prompt is None:
            prompt = ChatPromptTemplate.from_messages(
                [("system", "Write a concise summary of the following:\\n\\n{context}")]
            )

        self.chain = create_stuff_documents_chain(get_llm(), prompt)

    def run(self, documents: List[Document]) -> str:
        return self.chain.invoke({"context": documents})


class QuestionGenerator:
    def __init__(self, model: BaseLanguageModel, retriever: BaseRetriever):
        self.model = model
        self.retriever = retriever
        self.reduced_documents_chain = ReduceDocumentsChain()

    @staticmethod
    def _is_article_key(key: str) -> TypeGuard[ArticleKey]:
        return key in ["title", "objective", "introduction", "steps"]

    def _get_article_prop_or_title(self, article: Article, prop: ArticleKey):
        if self._is_article_key(prop):
            return article[prop]

        return article.get("title", None)

    def generate_dynamic_questions(self, objective_text: str, steps_text: str):
        system_prompt = """You are a Cisco support agent and an expert at explaining technical concepts in simple terms. Use the previous steps as context to inform what steps to take next but most importantly, pay attention to the last step.
    
        <format-instructions>
            {format_instructions}
        </format-instructions>
        """
        human_prompt = """Below is the objective of the article and the incremental list of steps. Given this information, return 3 questions a user might ask about the most recent step. Wrap the output in `json` tags
        
        <objective>
            {objective}
        </objective>
        
        <steps>
            {text}
        </steps>
        """
        parser = PydanticOutputParser(pydantic_object=QuestionResponse)
        prompt = ChatPromptTemplate.from_messages(
            [("system", system_prompt), ("human", human_prompt)]
        ).partial(format_instructions=parser.get_format_instructions())
        chain = prompt | self.model | parser
        questions_response: QuestionResponse = chain.invoke(
            {"objective": objective_text, "text": steps_text}
        )
        return [question.question for question in questions_response.questions]

    def generate_dynamic_answers(
        self, article_title: str, questions: List[str], steps_text: str
    ) -> List[str]:
        answers = []
        template = """Use the following pieces of context to answer the question at the end.
            If the context does not provide the information, do your best to give a helpful answer based on what is happening in the most recent step.
            If you don't know the answer, just say that you don't know, don't try to make up an answer.
            Use three sentences maximum and keep the answer as concise as possible. Do not include step numbers in your response, just include the sentences.
    
            <context>
                {context}
            </context>
            
            <steps>
                {steps}
            </steps>
            
            <question>
                {question}
            </question>
            
            Helpful Answer:
        """
        prompt = ChatPromptTemplate.from_template(template)
        cache = {}
        for question in questions:
            query = f"{article_title} {question}"
            documents = self.retriever.invoke(query)
            summarized_docs = []

            for doc in documents:
                doc_id = doc.metadata["doc_id"]
                if doc_id in cache:
                    summarized_docs.append(cache[doc_id])
                else:
                    summary = self.reduced_documents_chain.run([doc])
                    cache[doc_id] = summary
                    summarized_docs.append(summary)

            context = "\n".join(summarized_docs)
            # summarized_docs = self.reduced_documents_chain.run(documents)
            chain = prompt | self.model | StrOutputParser()
            answer = chain.invoke(
                {"context": context, "steps": steps_text, "question": question}
            )
            answers.append(str(answer).strip())
        return answers


class StaticAnswerGenerator:
    STATIC_QUESTIONS: ClassVar[List[str]] = [
        "I don't understand this step",
        "Help me troubleshoot this step",
        "Show best practices for this step",
    ]

    def __init__(self, model: BaseLanguageModel, retriever: BaseRetriever):
        self.model = model
        self.retriever = retriever
        self.reduce_documents_chain = ReduceDocumentsChain()

    def generate_static_answers(self, step_text: str) -> List[tuple[str, str]]:
        results = []
        # This is here because the step text will not change for each static question
        summarized_docs = self.reduce_documents_chain.run(
            self.retriever.invoke(step_text)
        )
        for question in self.STATIC_QUESTIONS:
            answer = self._answer(step_text, question, summarized_docs)
            qna_pair = (question, answer)
            results.append(qna_pair)
        return results

    def _answer(self, text: str, question: str, summarized_docs: str):

        template = """Use the following pieces of context to answer the query at the end about the step. If you don't know the answer, just say that you don't know, don't try to make up an answer. Use three sentences maximum and keep the answer as concise as possible.
        
        If you are asked to `Show Best Practices` for the step, and you do not know the answer or the context does not provide the information, you can simply say the user is already following best practices or use general knowledge to provide a best practice.
        If you are asked `I don't understand this step`, and the context does not provide the information, you can simply provide a general explanation of the step.
        
        Only answer `I don't know` if you are not confident in your understanding of the query and the context does not provide the information.
        
        <context>
            {context}
        </context>
        
        <query>
            {query}
        </query>
        
        <step>
            {step}
        </step>
        """
        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | self.model | StrOutputParser()
        static_answer = chain.invoke(
            {"context": summarized_docs, "query": question, "step": text}
        )
        return str(static_answer).strip()


class ArticleQuestionGenerator:
    def __init__(self, article: Article):
        self.article = article
        self.model = get_llm()
        retriever_initializer = ParentRetriever(CBS_220_ADMIN_GUIDE_COLLECTION)
        self.retriever = retriever_initializer.init_retriever()
        self.question_generator = QuestionGenerator(self.model, self.retriever)
        self.static_answer_generator = StaticAnswerGenerator(self.model, self.retriever)

    def process_article_steps(self) -> Article:
        title_text = self.article["title"]
        for i, step in enumerate(self.article["steps"]):
            steps_text = self._get_steps_text(i)
            dynamic_questions = self.question_generator.generate_dynamic_questions(
                title_text, steps_text
            )
            dynamic_answers = self.question_generator.generate_dynamic_answers(
                title_text, dynamic_questions, steps_text
            )
            dynamic_qna = list(zip(dynamic_questions, dynamic_answers))
            static_qna = self.static_answer_generator.generate_static_answers(
                step.get("text")
            )
            self._map_qna_to_step(dynamic_qna, static_qna, step)

        return self.article

    def _get_steps_text(self, index: int) -> str:
        return "".join(
            f"Step {j + 1}: {step['text']} \n"
            for j, step in enumerate(self.article["steps"][: index + 1])
        )

    def _map_qna_to_step(
        self, dynamic: List[tuple[str, str]], static: List[tuple[str, str]], step: Step
    ):
        for i, (question, answer) in enumerate(dynamic):
            step[f"dynamic_question_{i+1}"] = question
            step[f"dynamic_answer_{i+1}"] = answer

        for i, (question, answer) in enumerate(static):
            step[f"static_question_{i+1}"] = question
            step[f"static_answer_{i+1}"] = answer


try:
    test_article = json.loads(
        """{
            "series": "Cisco Business 220 Series Smart Switches",
            "title": "Configure SNMP Views on CBS220",
            "document_id": "1633447726598168",
            "category": "Configuration",
            "url": "http://www.cisco.com/c/en/us/support/docs/smb/switches/Cisco-Business-Switching/kmgmt2884-configure-snmp-views-cbs220.html",
            "objective": "This article provides instructions on how to configure the Simple Network Management Protocol (SNMP) Views on your Cisco Business 220 series switch.",
            "applicable_devices": [
                {
                    "device": "CBS220 series",
                    "software": "2.0.1.5",
                    "datasheet_link": "https://www.cisco.com/c/en/us/products/collateral/switches/business-220-series-smart-switches/datasheet-c78-744915.html",
                    "software_link": "https://software.cisco.com/download/home/286327375"
                }
            ],
            "introduction": "SNMP is an Internet-standard protocol used to manage devices on IP networks. The SNMP messages are used to inspect and communicate information about managed objects. SNMP uses Management Information Bases (MIBs) to store available objects in a hierarchical or tree-structured namespace that contains object identifiers (OIDs). An OID identifies the information in the MIB hierarchy that can be read or set via SNMP. SNMP Views are a subset of MIB objects that can be assigned to an SNMP access group to control write, read, and notification privileges of SNMP users over MIB object information. A view is a user-defined label for a collection of MIB subtrees. Each subtree ID is defined by the OID of the root of the relevant subtrees. Either well-known names can be used to specify the root of the desired subtree or an OID can be entered.",
            "steps": [
                {
                    "section": "Add an SNMP View",
                    "step_number": 1,
                    "text": "Log in to the web user interface (UI) of your switch.",
                    "src": "https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/Cisco-Business-Switching/images/kmgmt2884-configure-snmp-views-cbs220-image1.png",
                    "alt": "Related diagram, image, or screenshot",
                    "note": null,
                    "emphasized_text": [],
                    "emphasized_tags": []
                },
                {
                    "section": "Add an SNMP View",
                    "step_number": 2,
                    "text": "Choose SNMP > Views . The View Table displays the following information: <ul> <li> View Name - The name of the view. </li> <li> Object ID Subtree - The subtree to be included or excluded in the SNMP view. </li> <li> Object ID Subtree View - Displays whether the defined subtree is included or excluded in the selected SNMP view. </li> </ul>",
                    "src": "https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/Cisco-Business-Switching/images/kmgmt2884-configure-snmp-views-cbs220-image2a.png",
                    "alt": "Related diagram, image, or screenshot",
                    "note": null,
                    "emphasized_text": ["View Table"],
                    "emphasized_tags": ["i"]
                },
                {
                    "section": "Add an SNMP View",
                    "step_number": 3,
                    "text": "Click the Add button to to define new views.",
                    "src": "https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/Cisco-Business-Switching/images/kmgmt2884-configure-snmp-views-cbs220-image3.png",
                    "alt": "Related diagram, image, or screenshot",
                    "note": null,
                    "emphasized_text": ["Add"],
                    "emphasized_tags": ["b"]
                },
                {
                    "section": "Add an SNMP View",
                    "step_number": 4,
                    "text": "Enter the name of the new SNMP view in the View Name field. The character limit for this field is 32.",
                    "src": "https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/Cisco-Business-Switching/images/kmgmt2884-configure-snmp-views-cbs220-image4.png",
                    "alt": "Related diagram, image, or screenshot",
                    "note": null,
                    "emphasized_text": ["View Name"],
                    "emphasized_tags": ["i"]
                },
                {
                    "section": "Add an SNMP View",
                    "step_number": 5,
                    "text": "In the Object ID Subtree area, click one of the following radio buttons that defines a method to select a node in the MIB tree that is included or excluded in the new SNMP view. The options are: <ul> <li> Select from list - Allows you to choose the node in the MIB tree from the available list. </li> <li> User Defined - Allows the user to enter the object identifier that is not available in the Select From list. If this option is chosen, enter the OID in the <i> User Defined </i> field then skip to <a href=\' step9\'> Step 9 </a> . </li> </ul>",
                    "src": "https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/Cisco-Business-Switching/images/kmgmt2884-configure-snmp-views-cbs220-image5.png",
                    "alt": "Related diagram, image, or screenshot",
                    "note": "In this example, Select from list is chosen.",
                    "emphasized_text": [],
                    "emphasized_tags": []
                },
                {
                    "section": "Add an SNMP View",
                    "step_number": 6,
                    "text": "(Optional) Scroll down the list and choose an OID subtree from the list.",
                    "src": "https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/Cisco-Business-Switching/images/kmgmt2884-configure-snmp-views-cbs220-image6.png",
                    "alt": "Related diagram, image, or screenshot",
                    "note": null,
                    "emphasized_text": [],
                    "emphasized_tags": []
                },
                {
                    "section": "Add an SNMP View",
                    "step_number": 7,
                    "text": "(Optional) Use the Up arrow to go to the level of the parent and siblings of the chosen node and click the Down arrow to descend to the level of the children of the chosen node.",
                    "src": "https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/Cisco-Business-Switching/images/kmgmt2884-configure-snmp-views-cbs220-image7.png",
                    "alt": "Related diagram, image, or screenshot",
                    "note": null,
                    "emphasized_text": ["Up", "Down"],
                    "emphasized_tags": ["b", "b"]
                },
                {
                    "section": "Add an SNMP View",
                    "step_number": 8,
                    "text": "(Optional) Choose a child from the list. If the Up button is chosen in Step 7, choose the parent instead.",
                    "src": "https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/Cisco-Business-Switching/images/kmgmt2884-configure-snmp-views-cbs220-image8.png",
                    "alt": "Related diagram, image, or screenshot",
                    "note": null,
                    "emphasized_text": [],
                    "emphasized_tags": []
                },
                {
                    "section": "Add an SNMP View",
                    "step_number": 9,
                    "text": "Check or uncheck the Include in view check box. If this is checked, the chosen MIBs are included in the view, otherwise they are excluded.",
                    "src": "https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/Cisco-Business-Switching/images/kmgmt2884-configure-snmp-views-cbs220-image9.png",
                    "alt": "Related diagram, image, or screenshot",
                    "note": null,
                    "emphasized_text": ["Include in view"],
                    "emphasized_tags": ["b"]
                },
                {
                    "section": "Add an SNMP View",
                    "step_number": 10,
                    "text": "Click Apply then click Close .",
                    "src": "https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/Cisco-Business-Switching/images/kmgmt2884-configure-snmp-views-cbs220-image10.png",
                    "alt": "Related diagram, image, or screenshot",
                    "note": null,
                    "emphasized_text": ["Apply", "Close"],
                    "emphasized_tags": ["b", "b"]
                },
                {
                    "section": "Add an SNMP View",
                    "step_number": 11,
                    "text": "(Optional) Click Save to save the settings to the startup configuration file. You have now successfully added a new SNMP view in the View Table of your switch.",
                    "src": "https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/Cisco-Business-Switching/images/kmgmt2884-configure-snmp-views-cbs220-image12.png",
                    "alt": "Related diagram, image, or screenshot",
                    "note": null,
                    "emphasized_text": ["Save"],
                    "emphasized_tags": ["b"]
                },
                {
                    "section": "Delete an SNMP View",
                    "step_number": 1,
                    "text": "In the View Table , check the check box of the view that you want to delete.",
                    "src": "https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/Cisco-Business-Switching/images/kmgmt2884-configure-snmp-views-cbs220-image12.png",
                    "alt": "Related diagram, image, or screenshot",
                    "note": null,
                    "emphasized_text": ["View Table"],
                    "emphasized_tags": ["i"]
                },
                {
                    "section": "Delete an SNMP View",
                    "step_number": 2,
                    "text": "Click Delete .",
                    "src": "https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/Cisco-Business-Switching/images/kmgmt2884-configure-snmp-views-cbs220-image13.png",
                    "alt": "Related diagram, image, or screenshot",
                    "note": null,
                    "emphasized_text": ["Delete"],
                    "emphasized_tags": ["b"]
                },
                {
                    "section": "Delete an SNMP View",
                    "step_number": 3,
                    "text": "(Optional) Click Save to save the settings to the startup configuration file. You have now successfully deleted an SNMP view from the View Table of your Cisco Business 220 series switch.",
                    "src": "https://www.cisco.com/c/dam/en/us/support/docs/smb/switches/Cisco-Business-Switching/images/kmgmt2884-configure-snmp-views-cbs220-image11.png",
                    "alt": "Related diagram, image, or screenshot",
                    "note": null,
                    "emphasized_text": ["Save"],
                    "emphasized_tags": ["b"]
                }
            ],
            "revision_history": [
                {
                    "revision": 1.0,
                    "publish_date": "2021-10-05",
                    "comments": "Initial Release"
                }
            ],
            "type": "Article"
        }
    """
    )
except json.JSONDecodeError as e:
    print(e)
    print(e.pos)

if __name__ == "__main__":
    article = test_article
    generator = ArticleQuestionGenerator(article)
    new_article = generator.process_article_steps()
    title = "_".join([word.lower() for word in article["title"].split()])
    with open(f"data/cisco/questions/{title}.json", "w") as f:
        f.write(json.dumps(new_article, indent=4))


# class GenerateArticleQuestions:
#     STATIC_QUESTIONS: ClassVar[List[str]] = [
#         "I don't understand this step",
#         "Help me troubleshoot this step",
#         "Show best practices for this step",
#     ]

#     def __init__(self, article: Article):
#         self.article = article
#         self.model = get_llm()

#     def _initialize_retriever(self) -> ParentDocumentRetriever:
#         results = CHROMA_CLIENT.get_or_create_collection(
#             CBS_220_ADMIN_GUIDE_COLLECTION_NAME
#         ).get()
#         documents = [
#             Document(page_content=doc, metadata=meta)
#             for doc, meta in zip(results["documents"], results["metadatas"])
#         ]
#         retriever = ParentDocumentRetriever(
#             vectorstore=Chroma(
#                 collection_name=f"{CBS_220_ADMIN_GUIDE_COLLECTION_NAME}_langchain",
#                 embedding_function=OpenAIEmbeddings(),
#             ),
#             docstore=InMemoryStore(),
#             child_splitter=RecursiveCharacterTextSplitter(
#                 chunk_size=400, add_start_index=True
#             ),
#         )
#         ids = [doc["doc_id"] for doc in results["metadatas"]]
#         retriever.add_documents(documents, ids=ids)
#         return retriever

#     def process_steps(self) -> Article:
#         for i, step in enumerate(self.article["steps"]):
#             objective_text = self._get_title_text()
#             steps_text = self._get_steps_text(i)
#             questions = self._get_dynamic_questions(objective_text, steps_text)
#             answers = self._get_dynamic_answers(questions)
#             self._map_qna_to_step(questions, answers, step)
#             self._get_static_answers(step, step["text"])
#         return self.article

#     def _refine_documents(self, documents: List[Document]):

#         document_prompt = PromptTemplate(
#             input_variables=["page_content"], template="{page_content}"
#         )
#         document_var_name = "context"
#         prompt = PromptTemplate.from_template("Summarize this content: {context}")
#         llm = get_llm()
#         chain = LLMChain(llm=llm, prompt=prompt)
#         initial_response_name = "prev_response"
#         # The prompt here should take as an input variable the
#         # `document_var_name` as well as `initial_response_name`
#         prompt_refine = PromptTemplate.from_template(
#             "Here's your first summary: {prev_response}. "
#             "Now add to it based on the following context: {context}"
#         )
#         refine_chain = LLMChain(llm=llm, prompt=prompt_refine)
#         refine_documents_chain = RefineDocumentsChain(
#             document_prompt=document_prompt,
#             document_variable_name=document_var_name,
#             initial_llm_chain=chain,
#             initial_response_name=initial_response_name,
#             refine_llm_chain=refine_chain,
#         )
#         refined_documents = refine_documents_chain.invoke(documents)
#         if isinstance(refined_documents, list):
#             for i, doc in enumerate(refined_documents):
#                 print(f"Document {i+1}: {doc}")
#         elif isinstance(refined_documents, dict):
#             print(refined_documents)
#         else:
#             print("refine documents must be a string")
#             print(refined_documents)
#         print(type(refined_documents))
#         return refined_documents["output_text"]

#     def _get_title_text(self) -> str:
#         return self.article["title"]

#     def _get_steps_text(self, current_step_index: int) -> str:
#         return "".join(
#             f"Step {j + 1}: {step['text']} \n"
#             for j, step in enumerate(self.article["steps"][: current_step_index + 1])
#         )

#     def _get_dynamic_questions(self, objective_text: str, steps_text: str) -> List[str]:
#         parser = PydanticOutputParser(pydantic_object=QuestionResponse)
#         system_prompt = """You are a Cisco support agent and an expert at explaining technical concepts in simple terms. Use the previous steps as context to inform the what steps to take next but most importantly, pay attention to the last step.

#         <format-instructions>
#             {format_instructions}
#         </format-instructions>
#         """
#         human_prompt = """Below is the objective of the article and the incremental list of steps. Given this information, return 3 questions a user might ask about the last step only. Wrap the output in `json` tags

#         <objective>
#             {objective}
#         </objective>

#         <steps>
#             {text}
#         </steps>
#         """
#         prompt = ChatPromptTemplate.from_messages(
#             [("system", system_prompt), ("human", human_prompt)]
#         ).partial(format_instructions=parser.get_format_instructions())
#         chain = prompt | self.model | parser
#         questions_response = chain.invoke(
#             {"objective": objective_text, "text": steps_text}
#         )
#         return [question.question for question in questions_response.questions]

#     def _get_dynamic_answers(self, questions: List[str]) -> List[str]:

#         answers = []
#         template = """Use the following pieces of context to answer the question at the end.
#             If you don't know the answer, just say that you don't know, don't try to make up an answer.
#             Use three sentences maximum and keep the answer as concise as possible. Do not include step numbers in your response, just include the sentences.

#             <context>
#                 {context}
#             </context>

#             <question>
#                 {question}
#             </question>

#             Helpful Answer:
#         """
#         prompt = ChatPromptTemplate.from_template(template)
#         objective_text = self._get_title_text()
#         for question in questions:
#             query = f"{objective_text} {question}"
#             documents = self.retriever.invoke(query)
#             summarized_docs = self._refine_documents(documents)
#             formatted_docs = format_docs(documents)
#             chain = prompt | self.model | StrOutputParser()
#             answer = chain.invoke({"context": summarized_docs, "question": question})
#             answers.append(str(answer).strip())
#         return answers

#     def _map_qna_to_step(self, questions: List[str], answers: List[str], step: Step):
#         for i in range(len(questions)):
#             step[f"dynamic_question_{i+1}"] = questions[i]
#             step[f"dynamic_answer_{i+1}"] = answers[i]

#     def _get_static_answers(self, step: Step, step_text: str):
#         objective_text = self._get_title_text()
#         documents = self.retriever.invoke(f"{objective_text} {step_text}")
#         summarized_docs = self._refine_documents(documents)
#         for i, question in enumerate(self.STATIC_QUESTIONS):
#             step[f"static_question_{i+1}"] = question
#             step[f"static_answer_{i+1}"] = self._process_static(
#                 summarized_docs, step_text, question
#             )

#     def _process_static(self, documents: str, text: str, question: str):
#         template = """Use the following pieces of context to answer the query at the end about the step. If you don't know the answer, just say that you don't know, don't try to make up an answer. Use three sentences maximum and keep the answer as concise as possible.

#         If you are asked to `Show Best Practices` for the step, and you do not know the answer or the context does not provide the information, you can simply say the user is already following best practices or use general knowledge to provide a best practice.
#         If you are asked `I don't understand this step`, and the context does not provide the information, you can simply provide a general explanation of the step.

#         Only answer `I don't know` if you are not confident in your understanding of the query and the context does not provide the information.

#         <context>
#             {context}
#         </context>

#         <query>
#             {query}
#         </query>

#         <step>
#             {step}
#         </step>
#         """
#         prompt = ChatPromptTemplate.from_template(template)
#         chain = prompt | self.model | StrOutputParser()
#         static_answer = chain.invoke(
#             {"context": documents, "query": question, "step": text}
#         )
#         return str(static_answer).strip()


# if __name__ == "__main__":
#     import os

#     article = test_article
#     generator = GenerateArticleQuestions(article)
#     article = generator.process_steps()
#     with open(f"{os.getcwd()}/data/cisco/questions/questions.json", "w") as f:
#         f.write(json.dumps(article, indent=4))
