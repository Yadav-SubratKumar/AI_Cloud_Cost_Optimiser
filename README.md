# ☁️ AI Cloud Cost Optimiser

> An AI-assisted Azure cost optimisation platform built with React, FastAPI, SQLite, Azure CLI, and Google Gemini. It scans Azure resource groups, identifies potential cost-saving opportunities, and presents actionable recommendations with estimated savings.

---

## 📑 Table of Contents

- [Overview](#-overview)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Azure Configuration](#-azure-configuration)
- [AI Analysis](#-ai-analysis)
- [API](#-api)
- [Database](#-database)
- [Troubleshooting](#-troubleshooting)
- [Limitations](#-limitations)
- [License](#-license)

---

## 🧭 Overview

AI Cloud Cost Optimiser helps users analyse Azure resource groups and find potential cloud cost-optimisation opportunities.

Users can:

- Create an account and log in
- View available Azure resource groups
- Select a resource group for analysis
- Scan Azure resources
- Analyse resources with Google Gemini
- View optimisation recommendations and estimated savings
- Review previous analyses

The application provides recommendations for review and **does not automatically execute Azure changes**.

---

## 🏗️ Architecture

```text
┌────────────────────────────────────────────────────────────┐
│                 AI CLOUD COST OPTIMISER                    │
├────────────────────────┬───────────────────────────────────┤
│       Frontend         │             Backend               │
│                        │                                   │
│ React + TypeScript     │ FastAPI                           │
│ Vite                   │ Authentication                    │
│ React Router           │ Azure Scanner                     │
│ Axios                  │ Gemini AI Analyzer                │
│ Tailwind CSS           │ SQLite                            │
└────────────────────────┴───────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
       Microsoft Azure                 Google Gemini
          Azure CLI                    AI Analysis
```

### Analysis Flow

```text
Select Resource Group
        ↓
Azure Resource Scan
        ↓
Gemini Analysis
        ↓
Save Analysis
        ↓
Optimisation Report
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Vite |
| UI | Tailwind CSS |
| Backend | Python, FastAPI, Uvicorn |
| Authentication | JWT, bcrypt |
| Database | SQLite, aiosqlite |
| Cloud | Microsoft Azure, Azure CLI |
| AI | Google Gemini (`google-genai`) |
| Real-time | WebSockets |
| HTTP Client | Axios |

---

## 📁 Project Structure

```text
AI_Cloud_Cost_Optimiser/
│
├── backend/
│   ├── main.py
│   ├── auth.py
│   ├── db.py
│   ├── azure_scanner.py
│   ├── ai_analyzer.py
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── index.css
│   │   ├── components/
│   │   │   ├── Navbar.tsx
│   │   │   └── ProgressTracker.tsx
│   │   └── pages/
│   │       ├── Login.tsx
│   │       ├── Signup.tsx
│   │       ├── Dashboard.tsx
│   │       ├── History.tsx
│   │       └── Report.tsx
│   ├── package.json
│   └── vite.config.ts
│
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm
- Azure CLI
- Azure account with access to the resources
- Google Gemini API key

Check the installations:

```bash
python --version
node --version
npm --version
az --version
```

### Backend

```bash
cd backend

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt
```

Create `backend/.env` from `.env.example`:

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash
JWT_SECRET=your_secret
```

Start the backend:

```bash
uvicorn main:app --reload
```

API:

```text
http://localhost:8000
```

Swagger documentation:

```text
http://localhost:8000/docs
```

### Frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

---

## ☁️ Azure Configuration

Authenticate with Azure:

```bash
az login
```

Check the active account:

```bash
az account show
```

List available subscriptions:

```bash
az account list -o table
```

Select a subscription if required:

```bash
az account set --subscription "<SUBSCRIPTION_NAME_OR_ID>"
```

Verify resource groups:

```bash
az group list -o table
```

The current scanner uses the Windows Azure CLI path:

```text
C:\Program Files\Microsoft SDKs\Azure\CLI2\wbin\az.cmd
```

If Azure CLI is installed elsewhere, update the path in:

```text
backend/azure_scanner.py
```

---

## 🤖 AI Analysis

Google Gemini analyses the Azure resource information collected by the scanner.

The application can identify opportunities involving areas such as:

- Virtual machine configuration
- Idle or unnecessary resources
- Auto-shutdown
- Spot allocation
- Managed disks
- Unattached disks
- Storage redundancy
- Storage access tiers
- Lifecycle policies
- Other configuration-based cost opportunities

The generated report includes recommendations and estimated savings.

> Estimated savings are not guaranteed billing savings and should be validated before making infrastructure changes.

---

## 🔌 API

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/auth/signup` | Create account |
| `POST` | `/api/auth/login` | Login |
| `GET` | `/api/resource-groups` | Get Azure resource groups |
| `POST` | `/api/analyze/start` | Start an analysis |
| `POST` | `/api/analyze` | Run analysis |
| `GET` | `/api/history` | Get analysis history |
| `WS` | `/ws/progress/{analysis_id}` | Analysis progress |

Full API documentation is available at:

```text
http://localhost:8000/docs
```

---

## 🗄️ Database

The application uses SQLite with `aiosqlite`.

The database is created locally as:

```text
backend/app.db
```

It stores user accounts and completed analysis information, including resource group, status, findings, estimated savings, and analysis results.

---

## 🐛 Troubleshooting

### Azure CLI not found

```bash
az --version
```

If Azure CLI works in the terminal but not in the application, check the path in `backend/azure_scanner.py`.

### Azure authentication problems

```bash
az login
az account show
```

Make sure the selected Azure subscription contains the resource group you want to analyse.

### Gemini API key error

Check:

```text
backend/.env
```

and verify:

```env
GEMINI_API_KEY=your_gemini_api_key
```

Restart the backend after changing the `.env` file.

### Frontend cannot connect to backend

Make sure the backend is running:

```bash
uvicorn main:app --reload
```

Then check:

```text
http://localhost:8000/docs
```

---

## ⚠️ Limitations

- Savings are estimates, not guaranteed Azure billing savings.
- The application focuses on configuration-based optimisation rather than complete Azure Cost Management analysis.
- Comprehensive long-term CPU/memory utilisation analysis is not currently provided.
- Azure CLI recommendations are not automatically executed.
- The current Azure CLI path is Windows-specific.
- SQLite is intended for the current local/development use case.

---

## 📄 License

No explicit open-source license is currently included with this project.

Add an appropriate `LICENSE` file if the project is distributed publicly.
