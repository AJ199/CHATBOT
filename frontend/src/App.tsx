import React, { useEffect, useState } from "react";
import ChatWindow from "./components/ChatWindow";

export default function App() {
  const [convoId, setConvoId] = useState<string | null>(null);
  const backend = import.meta.env.VITE_BACKEND_URL || "http://localhost:8000";

  useEffect(() => {
    // create conversation on load
    (async () => {
      try {
        const resp = await fetch(`${backend}/api/create_conversation`, { method: "POST" });
        const j = await resp.json();
        setConvoId(j.conversation_id);
      } catch (e) {
        console.error("Failed to create conversation", e);
      }
    })();
  }, []);

  return (
    <div className="app-root">
      <header className="header">
        <h1>ChatGPT-like Demo</h1>
      </header>
      <main className="main">
        {convoId ? (
          <ChatWindow convoId={convoId} wsUrl={backend} />
        ) : (
          <div>Initializing...</div>
        )}
      </main>
    </div>
  );
}
