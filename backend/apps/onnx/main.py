import time


async def get_all_models():
    onnx_models = [
        {
            "id": "onnx-community/Qwen2.5-Coder-0.5B-Instruct",
            "name": "onnx-community/Qwen2.5-Coder-0.5B-Instruct",
            "object": "model",
            "created": int(time.time()),
            "owned_by": "onnx",
            "info": {"meta": {"task": "text-generation", "dtype": "q4"}},
        },
        {
            "id": "Xenova/Phi-3-mini-4k-instruct",
            "name": "Xenova/Phi-3-mini-4k-instruct",
            "object": "model",
            "created": int(time.time()),
            "owned_by": "onnx",
            "info": {"meta": {"task": "text-generation", "dtype": "fp16"}},
        },
        {
            "id": "onnx-community/Llama-3.2-1B-Instruct",
            "name": "onnx-community/Llama-3.2-1B-Instruct",
            "object": "model",
            "created": int(time.time()),
            "owned_by": "onnx",
            "info": {"meta": {"task": "text-generation", "dtype": None}},
        },
        {
            "id": "nomic-ai/nomic-embed-text-v1",
            "name": "nomic-ai/nomic-embed-text-v1",
            "object": "model",
            "created": int(time.time()),
            "owned_by": "onnx",
            "info": {
                "meta": {
                    "task": "sentence-similarity",
                    "dtype": None,
                    "context_length": 8192,
                    "task_instruction_prefixes": [
                        [
                            "search_document",
                            "Purpose: embed texts as documents from a dataset",
                        ],
                        ["search_query", "Purpose: embed texts as questions to answer"],
                        [
                            "clustering",
                            "Purpose: embed texts to group them into clusters (common topics, remove duplicates)",
                        ],
                        ["classification", "Purpose: embed texts to classify them"],
                    ],
                }
            },
        },
        {
            "id": "Xenova/all-MiniLM-L6-v2",
            "name": "Xenova/all-MiniLM-L6-v2",
            "object": "model",
            "created": int(time.time()),
            "owned_by": "onnx",
            "info": {
                "meta": {
                    "task": "feature-extraction",
                    "dtype": None,
                    "context_length": 768,
                }
            },
        },
    ]

    return onnx_models
