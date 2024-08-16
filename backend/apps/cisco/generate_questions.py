import json
from dotenv import find_dotenv, load_dotenv
from typing import TypedDict, List, Optional, Literal, Any, Dict, ClassVar
from backend.config import CHROMA_CLIENT, CATALYST_1300_ADMIN_GUIDE_COLLECTION_NAME
from langchain.pydantic_v1 import BaseModel
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.schema import Document
from langchain.retrievers.parent_document_retriever import ParentDocumentRetriever
from langchain.storage import InMemoryStore
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.apps.cisco.article_creator import query_database, create_or_retrieve_db

load_dotenv(find_dotenv(raise_error_if_not_found=True))


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


class GenerateArticleQuestions:
    STATIC_QUESTIONS: ClassVar[List[str]] = [
        "I don't understand this step",
        "Help me troubleshoot this step",
        "Show best practices for this step",
    ]

    def __init__(self, article: Article, query: str = None):
        self.article = article
        self.query = query
        self.model = get_llm()

        embedded_query = OpenAIEmbeddings().embed_query(text=query)
        results = CHROMA_CLIENT.get_or_create_collection(
            CATALYST_1300_ADMIN_GUIDE_COLLECTION_NAME
        ).get()
        documents = [
            Document(page_content=doc, metadata=meta)
            for doc, meta in zip(results["documents"], results["metadatas"])
        ]
        retriever = ParentDocumentRetriever(
            vectorstore=Chroma(
                collection_name=CATALYST_1300_ADMIN_GUIDE_COLLECTION_NAME
            ),
            docstore=InMemoryStore(),
            child_splitter=RecursiveCharacterTextSplitter(
                chunk_size=400, add_start_index=True
            ),
        )
        ids = [doc["doc_id"] for doc in results["metadatas"]]
        retriever.add_documents(documents, ids=ids)
        self.retriever = retriever

    def process_steps(self):

        for i, step in enumerate(self.article["steps"]):
            steps_text = "".join(
                f"Step {j + 1}: {step['text']} \n"
                for j, step in enumerate(self.article["steps"][: i + 1])
            )


test_article = json.loads(
    """{
	"title": "Configure Advanced Voice Quality of Service (QoS) on a Cisco Catalyst 1200 Switch",
	"objective": "The objective of this article is to guide through configuring Advanced Voice Quality of Service (QoS) on a Cisco Catalyst 1200 Switch using the Web-Based Utility.",
	"introduction": "Quality of Service (QoS) is a crucial feature in network management that prioritizes traffic flow based on the type of traffic. This is particularly important for latency-sensitive applications such as voice and video communications. By configuring Advanced Voice QoS on a Cisco Catalyst 1200 Switch, voice traffic is given higher priority, thereby improving the quality and reliability of voice calls. This configuration helps in managing network resources efficiently, reducing latency, and preventing packet loss. The Cisco Catalyst 1200 Switch supports advanced QoS settings that allow for detailed traffic management and policy implementation, making it an ideal choice for enterprise networks.",
	"steps": [
		{
			"section": "Configure QoS Properties",
			"step_number": 1,
			"text": "Log in to the web user interface (UI) of your switch.",
			"note": "The default username and password for the device is cisco/cisco."
		},
		{
			"section": "Configure QoS Properties",
			"step_number": 2,
			"text": "Navigate to Quality of Service > General > QoS Properties.",
			"note": null
		},
		{
			"section": "Configure QoS Properties",
			"step_number": 3,
			"text": "Set the QoS mode to Advanced.",
			"note": null
		},
		{
			"section": "Configure QoS Properties",
			"step_number": 4,
			"text": "Select Port/LAG and click Go to display/modify all ports/LAGs on the device and their CoS information.",
			"note": null
		},
		{
			"section": "Configure QoS Properties",
			"step_number": 5,
			"text": "Click Apply to update the Running Configuration file.",
			"note": null
		},
		{
			"section": "Set QoS on an Interface",
			"step_number": 1,
			"text": "Select the interface you want to configure and click Edit.",
			"note": null
		},
		{
			"section": "Set QoS on an Interface",
			"step_number": 2,
			"text": "Enter the parameters for the interface, including the Default CoS value for incoming packets that do not have a VLAN tag.",
			"note": "The default CoS is 0."
		},
		{
			"section": "Set QoS on an Interface",
			"step_number": 3,
			"text": "Click Apply to save the interface default CoS value to the Running Configuration file.",
			"note": null
		},
		{
			"section": "Add a QoS Policy",
			"step_number": 1,
			"text": "Navigate to Quality of Service > QoS Advanced Mode > Policy Table.",
			"note": null
		},
		{
			"section": "Add a QoS Policy",
			"step_number": 2,
			"text": "Click Add to open the Add Policy Table page.",
			"note": null
		},
		{
			"section": "Add a QoS Policy",
			"step_number": 3,
			"text": "Enter the name of the new policy in the New Policy Name field.",
			"note": null
		},
		{
			"section": "Add a QoS Policy",
			"step_number": 4,
			"text": "Click Apply to add the QoS policy profile and update the Running Configuration file.",
			"note": null
		},
		{
			"section": "Create an Access Control List (ACL)",
			"step_number": 1,
			"text": "Navigate to Access Control > IPv4 Based ACL.",
			"note": null
		},
		{
			"section": "Create an Access Control List (ACL)",
			"step_number": 2,
			"text": "Click Add to create a new ACL and give it a name, such as 'QoS Voice Traffic'.",
			"note": null
		},
		{
			"section": "Create an Access Control List (ACL)",
			"step_number": 3,
			"text": "Click Apply to create the ACL.",
			"note": null
		},
		{
			"section": "Create ACL Rules",
			"step_number": 1,
			"text": "Select the ACL name you created to proceed.",
			"note": null
		},
		{
			"section": "Create ACL Rules",
			"step_number": 2,
			"text": "Assign a priority of 5 and set the action to Permit.",
			"note": null
		},
		{
			"section": "Create ACL Rules",
			"step_number": 3,
			"text": "Set the protocol to Any and define the network by setting the source IP address and wildcard mask. For example, use 10.5.0.0 and 0.0.0.255 respectively.",
			"note": null
		},
		{
			"section": "Create ACL Rules",
			"step_number": 4,
			"text": "Set the destination IP address and type of service to Any.",
			"note": null
		},
		{
			"section": "Create ACL Rules",
			"step_number": 5,
			"text": "Click Apply to save the ACL rules.",
			"note": null
		},
		{
			"section": "Create Class Maps",
			"step_number": 1,
			"text": "Navigate to Quality of Service > QoS Advanced Mode > Class Mapping.",
			"note": null
		},
		{
			"section": "Create Class Maps",
			"step_number": 2,
			"text": "Click the plus icon to create a new class map for inbound traffic.",
			"note": null
		},
		{
			"section": "Create Class Maps",
			"step_number": 3,
			"text": "Enable the identification of traffic bound to the QoS ACL you created.",
			"note": null
		},
		{
			"section": "Create Class Maps",
			"step_number": 4,
			"text": "Repeat the process to create a class map for outbound traffic.",
			"note": null
		},
		{
			"section": "Create QoS Policies",
			"step_number": 1,
			"text": "Navigate to Quality of Service > QoS Advanced Mode > Policy Table.",
			"note": null
		},
		{
			"section": "Create QoS Policies",
			"step_number": 2,
			"text": "Click Add to create a new policy for inbound traffic.",
			"note": null
		},
		{
			"section": "Create QoS Policies",
			"step_number": 3,
			"text": "Assign the policy to the inbound class map and set the action type to Set CoS 5 for matching traffic.",
			"note": null
		},
		{
			"section": "Create QoS Policies",
			"step_number": 4,
			"text": "Click Apply to save the inbound QoS policy.",
			"note": null
		},
		{
			"section": "Create QoS Policies",
			"step_number": 5,
			"text": "Repeat the process to create a new policy for outbound traffic.",
			"note": null
		},
		{
			"section": "Create QoS Policies",
			"step_number": 6,
			"text": "Assign the policy to the outbound class map and set the action type to DSCP 46 for matching traffic.",
			"note": null
		},
		{
			"section": "Create QoS Policies",
			"step_number": 7,
			"text": "Click Apply to save the outbound QoS policy.",
			"note": null
		},
		{
			"section": "Bind the QoS Policy to an Interface",
			"step_number": 1,
			"text": "Navigate to Policy Binding under Policy Class Maps.",
			"note": null
		},
		{
			"section": "Bind the QoS Policy to an Interface",
			"step_number": 2,
			"text": "Select the relevant upstream port connected to your router, for example, Port 17.",
			"note": null
		},
		{
			"section": "Bind the QoS Policy to an Interface",
			"step_number": 3,
			"text": "Enable both the input and output policies for the selected port.",
			"note": null
		},
		{
			"section": "Bind the QoS Policy to an Interface",
			"step_number": 4,
			"text": "For the input, select the inbound QoS policy previously configured and set the default action to Permit Any.",
			"note": null
		},
		{
			"section": "Bind the QoS Policy to an Interface",
			"step_number": 5,
			"text": "For the output, select the outbound QoS policy and set the default action to Permit Any.",
			"note": null
		},
		{
			"section": "Bind the QoS Policy to an Interface",
			"step_number": 6,
			"text": "Click Apply to enforce the new policies.",
			"note": null
		},
		{
			"section": "Save Configuration",
			"step_number": 1,
			"text": "Click the Save icon to save the configurations to the startup configuration file.",
			"note": "This ensures that the configurations are retained after a reboot."
		}
	],
	"document_id": "d1e75bce-4b69-4688-baf2-af14b655e4f4",
	"revision_history": [
		{
			"revision": 1.0,
			"publish_date": "2024-08-16",
			"comments": "Initial article creation."
		}
	]
}
"""
)
