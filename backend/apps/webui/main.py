from fastapi import FastAPI, Depends
from fastapi.routing import APIRoute
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from apps.webui.routers import (
    articles,
    auths,
    users,
    chats,
    documents,
    tools,
    models,
    prompts,
    configs,
    memories,
    utils,
    files,
    functions,
    series,
)
from apps.webui.models.functions import Functions
from apps.webui.models.models import Models
from apps.webui.utils import load_function_module_by_id

from utils.misc import stream_message_template
from utils.task import prompt_template


from config import (
    WEBUI_BUILD_HASH,
    SHOW_ADMIN_DETAILS,
    ADMIN_EMAIL,
    WEBUI_AUTH,
    DEFAULT_MODELS,
    DEFAULT_PROMPT_SUGGESTIONS,
    DEFAULT_USER_ROLE,
    ENABLE_SIGNUP,
    USER_PERMISSIONS,
    WEBHOOK_URL,
    WEBUI_AUTH_TRUSTED_EMAIL_HEADER,
    WEBUI_AUTH_TRUSTED_NAME_HEADER,
    JWT_EXPIRES_IN,
    WEBUI_BANNERS,
    ENABLE_COMMUNITY_SHARING,
    AppConfig,
    OAUTH_USERNAME_CLAIM,
    OAUTH_PICTURE_CLAIM,
)

from apps.socket.main import get_event_call, get_event_emitter

import inspect
import uuid
import time
import json

from typing import Iterator, Generator, Optional
from pydantic import BaseModel

app = FastAPI()

origins = ["*"]

app.state.config = AppConfig()

app.state.config.ENABLE_SIGNUP = ENABLE_SIGNUP
app.state.config.JWT_EXPIRES_IN = JWT_EXPIRES_IN
app.state.AUTH_TRUSTED_EMAIL_HEADER = WEBUI_AUTH_TRUSTED_EMAIL_HEADER
app.state.AUTH_TRUSTED_NAME_HEADER = WEBUI_AUTH_TRUSTED_NAME_HEADER


app.state.config.SHOW_ADMIN_DETAILS = SHOW_ADMIN_DETAILS
app.state.config.ADMIN_EMAIL = ADMIN_EMAIL


app.state.config.DEFAULT_MODELS = DEFAULT_MODELS
app.state.config.DEFAULT_PROMPT_SUGGESTIONS = DEFAULT_PROMPT_SUGGESTIONS
app.state.config.DEFAULT_USER_ROLE = DEFAULT_USER_ROLE
app.state.config.USER_PERMISSIONS = USER_PERMISSIONS
app.state.config.WEBHOOK_URL = WEBHOOK_URL
app.state.config.BANNERS = WEBUI_BANNERS

app.state.config.ENABLE_COMMUNITY_SHARING = ENABLE_COMMUNITY_SHARING

app.state.config.OAUTH_USERNAME_CLAIM = OAUTH_USERNAME_CLAIM
app.state.config.OAUTH_PICTURE_CLAIM = OAUTH_PICTURE_CLAIM

app.state.MODELS = {}
app.state.TOOLS = {}
app.state.FUNCTIONS = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

##############################
#
#
# Mounted Routers (APIs)
#
#
##############################

app.include_router(configs.router, prefix="/configs", tags=["configs"])
app.include_router(articles.router, prefix="/articles", tags=["articles"])
app.include_router(auths.router, prefix="/auths", tags=["auths"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(chats.router, prefix="/chats", tags=["chats"])

app.include_router(documents.router, prefix="/documents", tags=["documents"])
app.include_router(models.router, prefix="/models", tags=["models"])
app.include_router(prompts.router, prefix="/prompts", tags=["prompts"])

app.include_router(memories.router, prefix="/memories", tags=["memories"])
app.include_router(files.router, prefix="/files", tags=["files"])
app.include_router(tools.router, prefix="/tools", tags=["tools"])
app.include_router(functions.router, prefix="/functions", tags=["functions"])

app.include_router(series.router, prefix="/series", tags=["series"])
app.include_router(utils.router, prefix="/utils", tags=["utils"])


@app.get("/")
async def get_status():
    return {
        "status": True,
        "auth": WEBUI_AUTH,
        "default_models": app.state.config.DEFAULT_MODELS,
        "default_prompt_suggestions": app.state.config.DEFAULT_PROMPT_SUGGESTIONS,
    }


async def get_pipe_models():
    pipes = Functions.get_functions_by_type("pipe", active_only=True)
    pipe_models = []

    for pipe in pipes:
        # Check if function is already loaded
        if pipe.id not in app.state.FUNCTIONS:
            function_module, function_type, frontmatter = load_function_module_by_id(
                pipe.id
            )
            app.state.FUNCTIONS[pipe.id] = function_module
        else:
            function_module = app.state.FUNCTIONS[pipe.id]

        if hasattr(function_module, "valves") and hasattr(function_module, "Valves"):
            valves = Functions.get_function_valves_by_id(pipe.id)
            function_module.valves = function_module.Valves(
                **(valves if valves else {})
            )

        # Check if function is a manifold
        if hasattr(function_module, "type"):
            if function_module.type == "manifold":
                manifold_pipes = []

                # Check if pipes is a function or a list
                if callable(function_module.pipes):
                    manifold_pipes = function_module.pipes()
                else:
                    manifold_pipes = function_module.pipes

                for p in manifold_pipes:
                    manifold_pipe_id = f'{pipe.id}.{p["id"]}'
                    manifold_pipe_name = p["name"]

                    if hasattr(function_module, "name"):
                        manifold_pipe_name = (
                            f"{function_module.name}{manifold_pipe_name}"
                        )

                    pipe_flag = {"type": pipe.type}
                    if hasattr(function_module, "ChatValves"):
                        pipe_flag["valves_spec"] = function_module.ChatValves.schema()

                    pipe_models.append(
                        {
                            "id": manifold_pipe_id,
                            "name": manifold_pipe_name,
                            "object": "model",
                            "created": pipe.created_at,
                            "owned_by": "openai",
                            "pipe": pipe_flag,
                        }
                    )
        else:
            pipe_flag = {"type": "pipe"}
            if hasattr(function_module, "ChatValves"):
                pipe_flag["valves_spec"] = function_module.ChatValves.schema()

            pipe_models.append(
                {
                    "id": pipe.id,
                    "name": pipe.name,
                    "object": "model",
                    "created": pipe.created_at,
                    "owned_by": "openai",
                    "pipe": pipe_flag,
                }
            )

    return pipe_models


async def generate_function_chat_completion(form_data, user):
    model_id = form_data.get("model")
    model_info = Models.get_model_by_id(model_id)

    metadata = None
    if "metadata" in form_data:
        metadata = form_data["metadata"]
        del form_data["metadata"]

    __event_emitter__ = None
    __event_call__ = None
    __task__ = None

    if metadata:
        if (
            metadata.get("session_id")
            and metadata.get("chat_id")
            and metadata.get("message_id")
        ):
            __event_emitter__ = await get_event_emitter(metadata)
            __event_call__ = await get_event_call(metadata)

        if metadata.get("task"):
            __task__ = metadata.get("task")

    if model_info:
        if model_info.base_model_id:
            form_data["model"] = model_info.base_model_id

        model_info.params = model_info.params.model_dump()

        if model_info.params:
            if model_info.params.get("temperature", None) is not None:
                form_data["temperature"] = float(model_info.params.get("temperature"))

            if model_info.params.get("top_p", None):
                form_data["top_p"] = int(model_info.params.get("top_p", None))

            if model_info.params.get("max_tokens", None):
                form_data["max_tokens"] = int(model_info.params.get("max_tokens", None))

            if model_info.params.get("frequency_penalty", None):
                form_data["frequency_penalty"] = int(
                    model_info.params.get("frequency_penalty", None)
                )

            if model_info.params.get("seed", None):
                form_data["seed"] = model_info.params.get("seed", None)

            if model_info.params.get("stop", None):
                form_data["stop"] = (
                    [
                        bytes(stop, "utf-8").decode("unicode_escape")
                        for stop in model_info.params["stop"]
                    ]
                    if model_info.params.get("stop", None)
                    else None
                )

        system = model_info.params.get("system", None)
        if system:
            system = prompt_template(
                system,
                **(
                    {
                        "user_name": user.name,
                        "user_location": (
                            user.info.get("location") if user.info else None
                        ),
                    }
                    if user
                    else {}
                ),
            )
            # Check if the payload already has a system message
            # If not, add a system message to the payload
            if form_data.get("messages"):
                for message in form_data["messages"]:
                    if message.get("role") == "system":
                        message["content"] = system + message["content"]
                        break
                else:
                    form_data["messages"].insert(
                        0,
                        {
                            "role": "system",
                            "content": system,
                        },
                    )

    else:
        pass

    async def job():
        pipe_id = form_data["model"]
        if "." in pipe_id:
            pipe_id, sub_pipe_id = pipe_id.split(".", 1)
        print(pipe_id)

        # Check if function is already loaded
        if pipe_id not in app.state.FUNCTIONS:
            function_module, function_type, frontmatter = load_function_module_by_id(
                pipe_id
            )
            app.state.FUNCTIONS[pipe_id] = function_module
        else:
            function_module = app.state.FUNCTIONS[pipe_id]

        if hasattr(function_module, "valves") and hasattr(function_module, "Valves"):

            valves = Functions.get_function_valves_by_id(pipe_id)
            function_module.valves = function_module.Valves(
                **(valves if valves else {})
            )

        pipe = function_module.pipe

        # Get the signature of the function
        sig = inspect.signature(pipe)
        params = {"body": form_data}

        if "__user__" in sig.parameters:
            __user__ = {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
            }

            try:
                if hasattr(function_module, "UserValves"):
                    __user__["valves"] = function_module.UserValves(
                        **Functions.get_user_valves_by_id_and_user_id(pipe_id, user.id)
                    )
            except Exception as e:
                print(e)

            params = {**params, "__user__": __user__}

        if "__event_emitter__" in sig.parameters:
            params = {**params, "__event_emitter__": __event_emitter__}

        if "__event_call__" in sig.parameters:
            params = {**params, "__event_call__": __event_call__}

        if "__task__" in sig.parameters:
            params = {**params, "__task__": __task__}

        if form_data["stream"]:

            async def stream_content():
                try:
                    if inspect.iscoroutinefunction(pipe):
                        res = await pipe(**params)
                    else:
                        res = pipe(**params)

                    # Directly return if the response is a StreamingResponse
                    if isinstance(res, StreamingResponse):
                        async for data in res.body_iterator:
                            yield data
                        return
                    if isinstance(res, dict):
                        yield f"data: {json.dumps(res)}\n\n"
                        return

                except Exception as e:
                    print(f"Error: {e}")
                    yield f"data: {json.dumps({'error': {'detail':str(e)}})}\n\n"
                    return

                if isinstance(res, str):
                    message = stream_message_template(form_data["model"], res)
                    yield f"data: {json.dumps(message)}\n\n"

                if isinstance(res, Iterator):
                    for line in res:
                        if isinstance(line, BaseModel):
                            line = line.model_dump_json()
                            line = f"data: {line}"
                        if isinstance(line, dict):
                            line = f"data: {json.dumps(line)}"

                        try:
                            line = line.decode("utf-8")
                        except:
                            pass

                        if line.startswith("data:"):
                            yield f"{line}\n\n"
                        else:
                            line = stream_message_template(form_data["model"], line)
                            yield f"data: {json.dumps(line)}\n\n"

                if isinstance(res, str) or isinstance(res, Generator):
                    finish_message = {
                        "id": f"{form_data['model']}-{str(uuid.uuid4())}",
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": form_data["model"],
                        "choices": [
                            {
                                "index": 0,
                                "delta": {},
                                "logprobs": None,
                                "finish_reason": "stop",
                            }
                        ],
                    }

                    yield f"data: {json.dumps(finish_message)}\n\n"
                    yield f"data: [DONE]"

            return StreamingResponse(stream_content(), media_type="text/event-stream")
        else:

            try:
                if inspect.iscoroutinefunction(pipe):
                    res = await pipe(**params)
                else:
                    res = pipe(**params)

                if isinstance(res, StreamingResponse):
                    return res
            except Exception as e:
                print(f"Error: {e}")
                return {"error": {"detail": str(e)}}

            if isinstance(res, dict):
                return res
            elif isinstance(res, BaseModel):
                return res.model_dump()
            else:
                message = ""
                if isinstance(res, str):
                    message = res
                if isinstance(res, Generator):
                    for stream in res:
                        message = f"{message}{stream}"

                return {
                    "id": f"{form_data['model']}-{str(uuid.uuid4())}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": form_data["model"],
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": message,
                            },
                            "logprobs": None,
                            "finish_reason": "stop",
                        }
                    ],
                }

    return await job()
