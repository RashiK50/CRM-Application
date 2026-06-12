# Agentic CRM Core

An enterprise-grade, autonomous Customer Relationship Management (CRM) system powered by LangGraph, Groq (Llama-3), and a standard RAG architecture. This system acts as a highly intelligent **Inbox Operator** that can ingest customer emails, semantically classify their intent, retrieve corporate knowledge to draft accurate responses, and autonomously resolve tickets or escalate them to human operators.

*Replace with an actual project screenshot.*

---

# Key Features

### Autonomous ReAct Agent

Utilizes LangGraph to power a continuous reasoning loop (**Think → Act → Observe**) that independently resolves customer inquiries.

### RAG Knowledge Base

Integrates ChromaDB and Google Gemini Embeddings to search company policies, rate limits, SLAs, and documentation for accurate contextual response generation.

### Smart Traffic Cop

An upfront LLM classifier that instantly filters spam, detects critical cyber threats, and accurately categorizes standard inquiries.

### Real-Time Analytics Hub

A React-powered dashboard featuring Recharts to track:

* Sentiment trends over time
* Request distribution
* Auto-replied tickets
* Human-resolved tickets
* Critical threats
* Escalation metrics

### Human-in-the-Loop (HITL)

Seamlessly hands off high-urgency or complex issues to a human operator queue where operators can review AI-generated drafts before committing responses.

---

# Technology Stack

## Backend

| Component        | Technology                         |
| ---------------- | ---------------------------------- |
| Framework        | FastAPI                            |
| Database         | SQLite + SQLAlchemy ORM            |
| AI Orchestration | LangGraph                          |
| LLM              | Groq API (Llama-3.3-70B-Versatile) |
| Embeddings       | Google Gemini Embeddings           |
| Vector Database  | ChromaDB                           |

## Frontend

| Component | Technology   |
| --------- | ------------ |
| Framework | React (Vite) |
| Styling   | Tailwind CSS |
| Icons     | Lucide React |
| Charts    | Recharts     |

---

# Project Structure

```text
CRM-Application/
│
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── config.py
│   │
│   ├── routers/
│   │   ├── dashboard.py
│   │   ├── respond.py
│   │   ├── threads.py
│   │   └── ...
│   │
│   └── services/
│       ├── agent.py
│       ├── agent_nodes.py
│       ├── agent_state.py
│       ├── agent_tools.py
│       ├── llm_classifier.py
│       └── rag_pipeline.py
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   │
│   │   ├── components/
│   │   │   └── AnalyticsDashboard.jsx
│   │   │
│   │   └── ...
│   │
│   ├── package.json
│   └── tailwind.config.js
│
└── README.md
```

---

# Getting Started

## Prerequisites

* Python 3.10+
* Node.js 18+
* Groq API Key
* Google Gemini API Key

---

## Backend Setup

### Create and activate a virtual environment

```bash
python -m venv venv
```

Linux/Mac:

```bash
source venv/bin/activate
```

Windows:

```bash
venv\Scripts\activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Configure environment variables

Create a `.env` file inside the `backend/` directory:

```env
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

### Start the FastAPI server

```bash
uvicorn backend.main:app --reload
```

Backend will be available at:

```text
http://127.0.0.1:8000
```

---

## Frontend Setup

Navigate to the frontend directory:

```bash
cd frontend
```

### Install dependencies

```bash
npm install
```

### Start the development server

```bash
npm run dev
```

Frontend will be available at:

```text
http://localhost:5173
```

---

# How It Works

## 1. Email Ingestion

An incoming customer email payload is sent to the backend API.

---

## 2. Traffic Cop Classification

The `LLMClassifierService` analyzes the email and determines whether it is:

* Spam
* Critical Security Threat
* Standard Customer Inquiry

Spam emails are discarded immediately.

---

## 3. Agentic ReAct Loop

For valid inquiries, the LangGraph-powered agent begins its reasoning cycle:

```text
Think → Act → Observe → Decide
```

The agent may invoke tools such as:

* RAG Knowledge Search
* Policy Retrieval
* SLA Verification
* Context Enrichment

---

## 4. Decision Making

Based on confidence and business rules:

| Scenario                           | Outcome         |
| ---------------------------------- | --------------- |
| High confidence + standard request | Auto-Replied    |
| Compliance-sensitive request       | Escalated       |
| Low confidence                     | Human Review    |
| Security incident / ransomware     | Critical Threat |

---

## 5. Human Operator Review

Escalated tickets appear in the operator dashboard.

Operators can:

* Review customer messages
* Inspect AI reasoning
* Edit drafted responses
* Approve and transmit replies

Upon approval, the ticket is marked as:

```text
Human Resolved
```

---

# Analytics Dashboard

The dashboard provides real-time operational visibility through:

* Request Distribution Analysis
* Sentiment Tracking
* Auto-Resolution Rate
* Human Escalation Metrics
* Critical Threat Monitoring
* RAG Retrieval Diagnostics

---

# Future Enhancements

* Multi-agent collaboration workflows
* Email provider integrations (Gmail, Outlook)
* CRM integrations (Salesforce, HubSpot)
* Advanced SLA monitoring
* Multi-language customer support
* Voice and chat support channels

---

# Built With

* Python
* FastAPI
* LangGraph
* Groq LLM
* Google Gemini Embeddings
* ChromaDB
* React
* Tailwind CSS

---

### Autonomous Customer Support Through Agentic AI
