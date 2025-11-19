# backend/app/api_chat.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from typing import Dict, Any
from ..store import ConversationStore
from ..core_llm import build_messages_for_llm, stream_completion_tokens
import asyncio

router = APIRouter()
store = ConversationStore()

@router.post("/create_conversation")
async def create_conversation():
    convo_id = store.create_conversation()
    return {"conversation_id": convo_id}

@router.post("/chat")
async def chat_non_stream(payload: Dict[str, Any]):
    """
    Simple non-streaming REST chat for quick testing:
    payload: { conversation_id, message }
    """
    convo_id = payload.get("conversation_id")
    text = payload.get("message")
    if not convo_id or not text:
        raise HTTPException(status_code=400, detail="conversation_id and message required")
    # append user message
    store.append_message(convo_id, "user", text)
    history = store.get_last_messages(convo_id, limit=12)
    messages = build_messages_for_llm(history)
    # call OpenAI in blocking manner (non-stream)
    import openai, os
    resp = openai.ChatCompletion.create(model="gpt-4o-mini", messages=messages, max_tokens=512)
    answer = resp["choices"][0]["message"]["content"]
    store.append_message(convo_id, "assistant", answer)
    return {"answer": answer}

@router.websocket("/ws/chat/{conversation_id}")
async def ws_chat(ws: WebSocket, conversation_id: str):
    """
    WebSocket streaming chat endpoint.
    Client sends JSON messages:
      { "type": "user_message", "text": "..." }
    Server streams JSON messages:
      { "type": "token", "text": "..." }
      { "type": "done" }
      { "type": "error", "message": "..." }
    """
    await ws.accept()
    try:
        while True:
            data = await ws.receive_json()
            if not data:
                continue
            typ = data.get("type")
            if typ == "user_message":
                user_text = data.get("text", "")
                if not user_text:
                    await ws.send_json({"type": "error", "message": "empty message"})
                    continue

                # append user message to store
                store.append_message(conversation_id, "user", user_text)

                # build messages for model
                history = store.get_last_messages(conversation_id, limit=12)
                messages = build_messages_for_llm(history)

                # stream tokens from LLM and forward them to websocket client
                assistant_accum = []
                try:
                    async for token in stream_completion_tokens(messages):
                        # send each token as it arrives
                        await ws.send_json({"type": "token", "text": token})
                        assistant_accum.append(token)
                    # once done, combine and store assistant final message
                    assistant_text = "".join(assistant_accum)
                    store.append_message(conversation_id, "assistant", assistant_text)
                    await ws.send_json({"type": "done"})
                except Exception as e:
                    await ws.send_json({"type": "error", "message": f"LLM stream error: {str(e)}"})
            else:
                # ignore unknown types for now
                await ws.send_json({"type":"error","message":"unknown message type"})
    except WebSocketDisconnect:
        return
    except Exception as e:
        try:
            await ws.send_json({"type":"error","message": f"server error: {str(e)}"})
        except Exception:
            pass
        return
