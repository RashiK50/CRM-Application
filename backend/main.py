from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import engine, Base
from backend.routers import ingest, threads, dashboard, respond, analytics, rag,agent, contacts, audit

# Automatically bootstrap SQLite database schemas on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Agentic CRM Operations Hub",
    description="Production-grade real-time email ingestion and multi-layer triage system.",
    version="2.0.0"
)

# Enable loose CORS boundaries for the React interface connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register endpoints from our routers
app.include_router(ingest.router)
app.include_router(threads.router)
app.include_router(dashboard.router)
app.include_router(respond.router)
app.include_router(analytics.router)
app.include_router(rag.router)
app.include_router(agent.router)
app.include_router(contacts.router)
app.include_router(audit.router)

@app.get("/")
def read_root():
    """System health check endpoint."""
    return {"status": "healthy", "service": "CRM Backend Engine"}