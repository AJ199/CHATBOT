# CHATBOT

A full-stack LLM-powered chatbot built with FastAPI, React, and Vite, featuring token-level streaming, modular API structure, and containerized deployment via Docker.

---

## Features

- Multi-turn conversational experience (in-memory session storage)  
- Token-level streaming responses via WebSocket (OpenAI → FastAPI → React)  
- Clean modular backend API design  
- Simple, quick frontend built with React + Vite  
- Docker + docker-compose support for local development and deployment  
- Ready for extension: swap out LLMs, plug in persistence, add auth, etc.

---

## Architecture & Tech Stack

- **Backend**: Python, FastAPI, WebSockets  
- **Frontend**: React, Vite, TypeScript  
- **Containerization**: Docker, docker-compose  
- **LLM**: Compatible with OpenAI API 
- **Session Handling**: In-memory for demo; ideal for quick prototype or small-scale use  
- **Streaming**: Tokens are pushed progressively to the frontend so the reply appears live  
- **Frontend UI**: Minimalistic, focusing on real-time conversational feel
