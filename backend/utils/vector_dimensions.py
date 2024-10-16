from enum import Enum


# vector length created by embedding fn
class VectorDimensions(Enum):
    GPT4ALL = 384
    OPENAI = 1536
    VERTEX_AI = 768
    HUGGING_FACE = 384
    GOOGLE_AI = 768
    MISTRAL_AI = 1024
    NVIDIA_AI = 1024
    COHERE = 384
    OLLAMA = 384
    AMAZON_TITAN_V1 = 1536
    AMAZON_TITAN_V2 = 1024


class EmbeddingFunctions(Enum):
    OPENAI = "OPENAI"
    HUGGING_FACE = "HUGGING_FACE"
    VERTEX_AI = "VERTEX_AI"
    AWS_BEDROCK = "AWS_BEDROCK"
    GPT4ALL = "GPT4ALL"
    OLLAMA = "OLLAMA"


class Providers(Enum):
    OPENAI = "OPENAI"
    ANTHROPHIC = "ANTHPROPIC"
    VERTEX_AI = "VERTEX_AI"
    GPT4ALL = "GPT4ALL"
    OLLAMA = "OLLAMA"
    AZURE_OPENAI = "AZURE_OPENAI"
