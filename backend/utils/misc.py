from pathlib import Path
import hashlib
import json
import re
from datetime import timedelta
from typing import Optional, List, Tuple
import uuid
import time


def use_pysqlite3():
    """
    Swap std-lib sqlite3 with pysqlite3.
    """
    import platform
    import sqlite3

    if platform.system() == "Linux" and sqlite3.sqlite_version_info < (3, 35, 0):
        try:
            # According to the Chroma team, this patch only works on Linux
            import datetime
            import subprocess
            import sys

            subprocess.check_call(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "pysqlite3-binary",
                    "--quiet",
                    "--disable-pip-version-check",
                ]
            )

            __import__("pysqlite3")
            sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")

            # Let the user know what happened.
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
            print(
                f"{current_time} [smbdevs] [INFO]",
                "Swapped std-lib sqlite3 with pysqlite3 for ChromaDb compatibility.",
                f"Your original version was {sqlite3.sqlite_version}.",
            )
        except Exception as e:
            # Escape all exceptions
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S,%f")[:-3]
            print(
                f"{current_time} [smbdevs] [ERROR]",
                "Failed to swap std-lib sqlite3 with pysqlite3 for ChromaDb compatibility.",
                "Error:",
                e,
            )


def get_last_user_message_item(messages: List[dict]) -> str:
    for message in reversed(messages):
        if message["role"] == "user":
            return message
    return None


def get_last_user_message(messages: List[dict]) -> str:
    message = get_last_user_message_item(messages)

    if message is not None:
        if isinstance(message["content"], list):
            for item in message["content"]:
                if item["type"] == "text":
                    return item["text"]
        return message["content"]
    return None


def get_last_assistant_message(messages: List[dict]) -> str:
    for message in reversed(messages):
        if message["role"] == "assistant":
            if isinstance(message["content"], list):
                for item in message["content"]:
                    if item["type"] == "text":
                        return item["text"]
            return message["content"]
    return None


def get_system_message(messages: List[dict]) -> dict:
    for message in messages:
        if message["role"] == "system":
            return message
    return None


def remove_system_message(messages: List[dict]) -> List[dict]:
    return [message for message in messages if message["role"] != "system"]


def pop_system_message(messages: List[dict]) -> Tuple[dict, List[dict]]:
    return get_system_message(messages), remove_system_message(messages)


def add_or_update_system_message(content: str, messages: List[dict]):
    """
    Adds a new system message at the beginning of the messages list
    or updates the existing system message at the beginning.

    :param content: The message to be added or appended.
    :param messages: The list of message dictionaries.
    :return: The updated list of message dictionaries.
    """

    if messages and messages[0].get("role") == "system":
        messages[0]["content"] += f"{content}\n{messages[0]['content']}"
    else:
        # Insert at the beginning
        messages.insert(0, {"role": "system", "content": content})

    return messages


def stream_message_template(model: str, message: str):
    return {
        "id": f"{model}-{str(uuid.uuid4())}",
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "delta": {"content": message},
                "logprobs": None,
                "finish_reason": None,
            }
        ],
    }


def get_gravatar_url(email):
    # Trim leading and trailing whitespace from
    # an email address and force all characters
    # to lower case
    address = str(email).strip().lower()

    # Create a SHA256 hash of the final string
    hash_object = hashlib.sha256(address.encode())
    hash_hex = hash_object.hexdigest()

    # Grab the actual image URL
    return f"https://www.gravatar.com/avatar/{hash_hex}?d=mp"


def calculate_sha256(file):
    sha256 = hashlib.sha256()
    # Read the file in chunks to efficiently handle large files
    for chunk in iter(lambda: file.read(8192), b""):
        sha256.update(chunk)
    return sha256.hexdigest()


def calculate_sha256_string(string):
    # Create a new SHA-256 hash object
    sha256_hash = hashlib.sha256()
    # Update the hash object with the bytes of the input string
    sha256_hash.update(string.encode("utf-8"))
    # Get the hexadecimal representation of the hash
    hashed_string = sha256_hash.hexdigest()
    return hashed_string


def validate_email_format(email: str) -> bool:
    if email.endswith("@localhost"):
        return True

    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))


def sanitize_filename(file_name):
    # Convert to lowercase
    lower_case_file_name = file_name.lower()

    # Remove special characters using regular expression
    sanitized_file_name = re.sub(r"[^\w\s]", "", lower_case_file_name)

    # Replace spaces with dashes
    final_file_name = re.sub(r"\s+", "-", sanitized_file_name)

    return final_file_name


def extract_folders_after_data_docs(path):
    # Convert the path to a Path object if it's not already
    path = Path(path)

    # Extract parts of the path
    parts = path.parts

    # Find the index of '/data/docs' in the path
    try:
        index_data_docs = parts.index("data") + 1
        index_docs = parts.index("docs", index_data_docs) + 1
    except ValueError:
        return []

    # Exclude the filename and accumulate folder names
    tags = []

    folders = parts[index_docs:-1]
    for idx, part in enumerate(folders):
        tags.append("/".join(folders[: idx + 1]))

    return tags


def parse_duration(duration: str) -> Optional[timedelta]:
    if duration == "-1" or duration == "0":
        return None

    # Regular expression to find number and unit pairs
    pattern = r"(-?\d+(\.\d+)?)(ms|s|m|h|d|w)"
    matches = re.findall(pattern, duration)

    if not matches:
        raise ValueError("Invalid duration string")

    total_duration = timedelta()

    for number, _, unit in matches:
        number = float(number)
        if unit == "ms":
            total_duration += timedelta(milliseconds=number)
        elif unit == "s":
            total_duration += timedelta(seconds=number)
        elif unit == "m":
            total_duration += timedelta(minutes=number)
        elif unit == "h":
            total_duration += timedelta(hours=number)
        elif unit == "d":
            total_duration += timedelta(days=number)
        elif unit == "w":
            total_duration += timedelta(weeks=number)

    return total_duration


def parse_ollama_modelfile(model_text):
    parameters_meta = {
        "mirostat": int,
        "mirostat_eta": float,
        "mirostat_tau": float,
        "num_ctx": int,
        "repeat_last_n": int,
        "repeat_penalty": float,
        "temperature": float,
        "seed": int,
        "tfs_z": float,
        "num_predict": int,
        "top_k": int,
        "top_p": float,
        "num_keep": int,
        "typical_p": float,
        "presence_penalty": float,
        "frequency_penalty": float,
        "penalize_newline": bool,
        "numa": bool,
        "num_batch": int,
        "num_gpu": int,
        "main_gpu": int,
        "low_vram": bool,
        "f16_kv": bool,
        "vocab_only": bool,
        "use_mmap": bool,
        "use_mlock": bool,
        "num_thread": int,
    }

    data = {"base_model_id": None, "params": {}}

    # Parse base model
    base_model_match = re.search(
        r"^FROM\s+(\w+)", model_text, re.MULTILINE | re.IGNORECASE
    )
    if base_model_match:
        data["base_model_id"] = base_model_match.group(1)

    # Parse template
    template_match = re.search(
        r'TEMPLATE\s+"""(.+?)"""', model_text, re.DOTALL | re.IGNORECASE
    )
    if template_match:
        data["params"] = {"template": template_match.group(1).strip()}

    # Parse stops
    stops = re.findall(r'PARAMETER stop "(.*?)"', model_text, re.IGNORECASE)
    if stops:
        data["params"]["stop"] = stops

    # Parse other parameters from the provided list
    for param, param_type in parameters_meta.items():
        param_match = re.search(rf"PARAMETER {param} (.+)", model_text, re.IGNORECASE)
        if param_match:
            value = param_match.group(1)

            try:
                if param_type == int:
                    value = int(value)
                elif param_type == float:
                    value = float(value)
                elif param_type == bool:
                    value = value.lower() == "true"
            except Exception as e:
                print(e)
                continue

            data["params"][param] = value

    # Parse adapter
    adapter_match = re.search(r"ADAPTER (.+)", model_text, re.IGNORECASE)
    if adapter_match:
        data["params"]["adapter"] = adapter_match.group(1)

    # Parse system description
    system_desc_match = re.search(
        r'SYSTEM\s+"""(.+?)"""', model_text, re.DOTALL | re.IGNORECASE
    )
    system_desc_match_single = re.search(
        r"SYSTEM\s+([^\n]+)", model_text, re.IGNORECASE
    )

    if system_desc_match:
        data["params"]["system"] = system_desc_match.group(1).strip()
    elif system_desc_match_single:
        data["params"]["system"] = system_desc_match_single.group(1).strip()

    # Parse messages
    messages = []
    message_matches = re.findall(r"MESSAGE (\w+) (.+)", model_text, re.IGNORECASE)
    for role, content in message_matches:
        messages.append({"role": role, "content": content})

    if messages:
        data["params"]["messages"] = messages

    return data
