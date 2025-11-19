import React, { useEffect, useRef, useState } from "react";

type Message = { id: string; role: "user" | "assistant"; text: string };

export default function ChatWindow({ convoId, wsUrl }: { convoId: string; wsUrl: string }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const wsRef = useRef<WebSocket | null>(null);
  const assistantBuffer = useRef("");

  useEffect(() => {
    const wsScheme = wsUrl.startsWith("https") ? "wss" : "ws";
    const wsEndpoint = `${wsUrl.replace(/^http(s?):/, "")}/api/ws/chat/${convoId}`;
    const ws = new WebSocket(`${wsScheme}:${wsEndpoint}`);
    ws.onopen = () => console.log("WebSocket open");
    ws.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data);
        if (data.type === "token") {
          assistantBuffer.current += data.text;
          setMessages(prev => {
            const last = prev[prev.length - 1];
            if (last?.role === "assistant") {
              // update last assistant message content
              return [...prev.slice(0, -1), { ...last, text: assistantBuffer.current }];
            } else {
              return [...prev, { id: cryptoRandomId(), role: "assistant", text: assistantBuffer.current }];
            }
          });
        } else if (data.type === "done") {
          assistantBuffer.current = "";
        } else if (data.type === "error") {
          setMessages(prev => [...prev, { id: cryptoRandomId(), role: "assistant", text: "Error: " + data.message }]);
        }
      } catch (e) {
        console.error("ws message parse error", e);
      }
    };
    ws.onerror = (e) => console.error("ws error", e);
    ws.onclose = () => console.log("ws closed");
    wsRef.current = ws;
    return () => {
      ws.close();
    };
  }, [convoId, wsUrl]);

  function cryptoRandomId() {
    // cross-browser safe fallback
    if (typeof crypto !== "undefined" && crypto.randomUUID) return crypto.randomUUID();
    return Math.random().toString(36).slice(2, 11);
  }

  function sendMessage() {
    const msg = input.trim();
    if (!msg) return;
    // append user message locally
    setMessages(prev => [...prev, { id: cryptoRandomId(), role: "user", text: msg }]);
    // send via websocket
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      setMessages(prev => [...prev, { id: cryptoRandomId(), role: "assistant", text: "Error: connection not open" }]);
      setInput("");
      return;
    }
    wsRef.current.send(JSON.stringify({ type: "user_message", text: msg }));
    setInput("");
  }

  return (
    <div className="chat-root">
      <div className="messages" id="messages">
        {messages.map(m => (
          <div key={m.id} className={`message ${m.role === "user" ? "user" : "assistant"}`}>
            <div className="bubble">{m.text}</div>
          </div>
        ))}
      </div>
      <div className="composer">
        <input
          placeholder="Type a message and press Enter..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              sendMessage();
            }
          }}
        />
        <button onClick={sendMessage}>Send</button>
      </div>
    </div>
  );
}
