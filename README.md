# AI Cloud Cost Optimiser

A FastAPI + React tool that scans Azure resource groups and uses GPT-4o to identify cost-saving opportunities.

## Stack

- **Backend**: FastAPI, , SQLite , google.genai, JWT auth, WebSocket progress
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS

## Prerequisites

- Python 3.11+
- Node.js 18+
- Azure CLI installed and authenticated (`az login`)
- An OpenAI API key

## Backend Setup

```bash
cd backend
cp .env.example .env
# Edit .env — set JWT_SECRET and OPENAI_API_KEY
pip install -r requirements.txt
uvicorn main:app --reload
```

The SQLite database (`backend/app.db`) is created automatically on first run. No PostgreSQL needed.

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173
