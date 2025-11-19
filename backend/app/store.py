# backend/app/store.py
from typing import Dict, List
from dataclasses import dataclass, field
import time
import uuid

@dataclass
class Message:
    id: str
    role: str  # "user" or "assistant" or "system"
    text: str
    ts: float = field(default_factory=time.time)

class ConversationStore:
    def __init__(self):
        # conversation_id -> list[Message]
        self.store: Dict[str, List[Message]] = {}

    def create_conversation(self) -> str:
        convo_id = str(uuid.uuid4())
        self.store[convo_id] = []
        return convo_id

    def append_message(self, convo_id: str, role: str, text: str) -> Message:
        if convo_id not in self.store:
            self.store[convo_id] = []
        msg = Message(id=str(uuid.uuid4()), role=role, text=text)
        self.store[convo_id].append(msg)
        return msg

    def get_last_messages(self, convo_id: str, limit:int=12):
        msgs = self.store.get(convo_id, [])
        return msgs[-limit:]

    def reset_conversation(self, convo_id: str):
        self.store[convo_id] = []
