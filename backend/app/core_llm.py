# backend/app/core_llm.py
import os
import openai
import asyncio
from typing import List, Dict, Any

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("Missing OPENAI_API_KEY environment variable")
openai.api_key = OPENAI_API_KEY

# Default model — change if you prefer
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

# Compose messages for the LLM from our internal messages
def build_messages_for_llm(history):
    # history is list of Message dataclass-like objects with .role and .text
    messages = []
    # optional system message for consistent persona
    messages.append({"role": "system", "content": "You are a helpful assistant named Athena. Be concise and helpful."})
    for m in history:
        role = "user" if m.role == "user" else "assistant"
        messages.append({"role": role, "content": m.text})
    return messages

# Blocking iterator over streaming events from OpenAI ChatCompletion
def _openai_streaming_generator(messages):
    """
    Calls openai.ChatCompletion.create(..., stream=True) and yields token strings as they arrive.
    This function is blocking and meant to be run in a thread with asyncio.to_thread.
    """
    # NOTE: using ChatCompletion endpoint with stream=True
    resp = openai.ChatCompletion.create(model=LLM_MODEL, messages=messages, stream=True)
    # resp is an iterator of events
    for event in resp:
        # event is a dict; content typically in event['choices'][0]['delta'].get('content', '')
        try:
            choices = event.get("choices", [])
            if not choices:
                continue
            delta = choices[0].get("delta", {})
            token = delta.get("content")
            if token:
                yield token
        except Exception:
            # skip non-content events
            continue

async def stream_completion_tokens(messages):
    """
    Async generator that yields token strings as they arrive by running the blocking
    generator in a thread using asyncio.to_thread.
    """
    loop = asyncio.get_running_loop()
    gen = await loop.run_in_executor(None, lambda: _openai_streaming_generator(messages))
    # `gen` here is a generator object; iterate it in a thread again to get tokens (safest)
    def iter_gen():
        for t in gen:
            yield t
    # Now run iteration in executor and yield tokens asynchronously
    it = iter_gen()
    while True:
        token = await loop.run_in_executor(None, lambda: next(it, None))
        if token is None:
            break
        yield token
