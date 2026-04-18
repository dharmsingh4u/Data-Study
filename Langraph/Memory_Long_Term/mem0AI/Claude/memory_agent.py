"""
Core memory + LLM logic for the AI Interview Prep Coach.

Public API:
    chat(user_id, user_message) -> str
    get_all_memories(user_id) -> dict
    health_check() -> dict
"""

import atexit
import logging
import os
import re
import sys
import threading
from pathlib import Path
from typing import Any

sys.path.insert(1, r'D:\Notebooks\LLM\env')
from enviorment import load_env
load_env()

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

# ---------------------------------------------------------------------------
# Bootstrap — env vars must be set before mem0 is imported
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent
#load_dotenv(dotenv_path=PROJECT_ROOT / ".env")
os.environ.setdefault("MEM0_DIR", str(PROJECT_ROOT / ".mem0"))
#os.environ.setdefault("MEM0_TELEMETRY", "False")

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration (all overridable via environment variables)
# ---------------------------------------------------------------------------

GEMINI_CHAT_MODEL = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash-lite")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001")
EMBEDDING_DIMS = int(os.getenv("EMBEDDING_DIMS", "768"))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "mem0_interview_prep")
MEMORY_SEARCH_LIMIT = int(os.getenv("MEMORY_SEARCH_LIMIT", "5"))

MAX_USER_ID_LEN = 64
MAX_MESSAGE_LEN = 4_096
_USER_ID_RE = re.compile(r"^[a-zA-Z0-9_\-\.]+$")

# ---------------------------------------------------------------------------
# Custom exceptions
# ---------------------------------------------------------------------------


class AgentError(Exception):
    """Base error raised by this module."""


class SetupError(AgentError):
    """Memory backend failed to initialise."""


class ValidationError(AgentError):
    """Caller supplied invalid input."""


# ---------------------------------------------------------------------------
# Input validation helpers
# ---------------------------------------------------------------------------


def _validate_user_id(user_id: str) -> None:
    if not user_id or not user_id.strip():
        raise ValidationError("user_id must not be empty.")
    if len(user_id) > MAX_USER_ID_LEN:
        raise ValidationError(f"user_id must be ≤ {MAX_USER_ID_LEN} characters.")
    if not _USER_ID_RE.match(user_id):
        raise ValidationError(
            "user_id may only contain letters, digits, underscores, hyphens, and dots."
        )


def _validate_message(message: str) -> None:
    if not message or not message.strip():
        raise ValidationError("Message must not be empty.")
    if len(message) > MAX_MESSAGE_LEN:
        raise ValidationError(f"Message must be ≤ {MAX_MESSAGE_LEN} characters.")


# ---------------------------------------------------------------------------
# LLM chain
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are an AI interview prep coach. Use the following memories about the candidate \
to personalise your questions, avoid repeating covered topics, and focus on their \
weak areas and target role.

Candidate memories:
{memories}

Based on this, either:
  (a) ask the next interview question tailored to them, or
  (b) evaluate their answer and give concise, actionable feedback.

Be specific and concise. Never repeat a question already in the memories.\
"""

_CHAIN = (
    ChatPromptTemplate.from_messages(
        [
            ("system", _SYSTEM_PROMPT),
            ("human", "{question}"),
        ]
    )
    | ChatGoogleGenerativeAI(model=GEMINI_CHAT_MODEL, temperature=0.3)
    | StrOutputParser()
)

# ---------------------------------------------------------------------------
# Memory singleton — lazy, thread-safe initialisation
# ---------------------------------------------------------------------------

_MEM0_CONFIG: dict[str, Any] = {
    "llm": {
        "provider": "gemini",
        "config": {"model": GEMINI_CHAT_MODEL, "temperature": 0.1},
    },
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": QDRANT_COLLECTION,
            "embedding_model_dims": EMBEDDING_DIMS,
            "path": str(PROJECT_ROOT / "qdrant_data"),
        },
    },
    "embedder": {
        "provider": "gemini",
        "config": {
            "model": GEMINI_EMBEDDING_MODEL,
            "embedding_dims": EMBEDDING_DIMS,
        },
    },
}

_memory_lock = threading.Lock()
_MEMORY: Any = None
_MEMORY_INIT_ERROR: Exception | None = None


def _get_memory() -> Any:
    """Return the Memory singleton, initialising it on first call."""
    global _MEMORY, _MEMORY_INIT_ERROR
    if _MEMORY is not None:
        return _MEMORY
    with _memory_lock:
        if _MEMORY is not None:  # double-checked locking
            return _MEMORY
        try:
            from mem0 import Memory  # import deferred so env vars are set first

            _MEMORY = Memory.from_config(_MEM0_CONFIG)
            logger.info("Mem0 memory backend initialised.")
        except Exception as exc:
            _MEMORY_INIT_ERROR = exc
            logger.error("Failed to initialise Mem0: %s", exc)
    return _MEMORY


def _close_memory() -> None:
    """Gracefully tear down the Qdrant client on process exit."""
    if _MEMORY is None:
        return
    for fn in (
        lambda: _MEMORY.vector_store.client.close(),
        lambda: _MEMORY.close(),
    ):
        try:
            fn()
        except Exception:
            pass
    logger.info("Mem0 memory backend closed.")


atexit.register(_close_memory)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _format_memories(search_results: Any) -> str:
    items = (
        search_results.get("results", [])
        if isinstance(search_results, dict)
        else search_results
    )
    lines = [
        f"- {item['memory']}"
        for item in items
        if isinstance(item, dict) and item.get("memory")
    ]
    return "\n".join(lines) if lines else "(no prior memories yet)"


def _invoke_chain_with_retry(memories: str, question: str) -> str:
    """Call the LangChain chain with exponential-backoff retry on transient errors."""

    @retry(
        retry=retry_if_exception_type(Exception),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    def _call() -> str:
        return _CHAIN.invoke({"memories": memories, "question": question})

    return _call()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def chat(user_id: str, user_message: str) -> str:
    """
    Fetch relevant memories, call the LLM, persist the exchange, and return
    the assistant reply.

    Raises:
        ValidationError: if *user_id* or *user_message* are invalid.
        SetupError: if the memory backend is unavailable.
        AgentError: for any other unexpected failure.
    """
    _validate_user_id(user_id)
    _validate_message(user_message)

    memory = _get_memory()
    if memory is None:
        raise SetupError(f"Memory backend unavailable: {_MEMORY_INIT_ERROR}")

    logger.info("chat() user=%r message_len=%d", user_id, len(user_message))

    try:
        search_results = memory.search(
            query=user_message, user_id=user_id, limit=MEMORY_SEARCH_LIMIT
        )
        memories_text = _format_memories(search_results)

        reply = _invoke_chain_with_retry(memories=memories_text, question=user_message)

        memory.add(
            [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": reply},
            ],
            user_id=user_id,
        )
        logger.debug("Memory updated for user=%r", user_id)
        return reply

    except (ValidationError, SetupError):
        raise
    except Exception as exc:
        logger.exception("Unexpected error in chat() for user=%r", user_id)
        raise AgentError(f"Chat failed: {exc}") from exc


def get_all_memories(user_id: str) -> dict:
    """
    Return all memories stored for *user_id*.

    Always returns a dict with at minimum a ``"results"`` key. On failure the
    dict also contains an ``"error"`` key with a human-readable message.
    """
    _validate_user_id(user_id)
    memory = _get_memory()
    if memory is None:
        return {"error": str(_MEMORY_INIT_ERROR), "results": []}
    try:
        return memory.get_all(user_id=user_id)
    except Exception as exc:
        logger.exception("get_all_memories() failed for user=%r", user_id)
        return {"error": str(exc), "results": []}


def health_check() -> dict:
    """
    Return a health-status dict.

    Returns:
        ``{"status": "healthy", "detail": "..."}`` or
        ``{"status": "unhealthy", "detail": "..."}``
    """
    memory = _get_memory()
    if memory is None:
        return {"status": "unhealthy", "detail": str(_MEMORY_INIT_ERROR)}
    return {"status": "healthy", "detail": "Mem0 backend ready."}
