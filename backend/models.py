import datetime
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, Numeric, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from database import Base

class Contact(Base):
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    company = Column(String(255), nullable=True)
    status = Column(String(50), default="Active")  # VIP, Blocked, Active, Churned
    account_value = Column(Numeric(12, 2), default=0.00)
    churn_risk_score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_contact_at = Column(DateTime, default=datetime.datetime.utcnow)

    threads = relationship("Thread", back_populates="contact")

class Thread(Base):
    __tablename__ = "threads"
    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(String(255), unique=True, nullable=False, index=True)
    subject = Column(String(255), nullable=True)
    sender_email = Column(String(255), ForeignKey("contacts.email"), nullable=False)
    first_seen_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_updated_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(50), default="Open")  # Open, Resolved, Escalated, Ignored
    assigned_to = Column(String(255), nullable=True)

    contact = relationship("Contact", back_populates="threads")
    emails = relationship("Email", back_populates="thread_node")

class Email(Base):
    __tablename__ = "emails"
    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(String(255), ForeignKey("threads.thread_id"), nullable=False)
    message_id = Column(String(255), unique=True, nullable=False, index=True)
    sender = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=True)
    body = Column(Text, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    sentiment_score = Column(Float, default=0.0)
    category = Column(String(100), nullable=True)
    urgency = Column(String(50), default="Low")  # Critical, High, Medium, Low
    requires_human = Column(Boolean, default=False)
    confidence = Column(Float, default=1.0)
    raw_entities = Column(JSON, default=dict)
    status = Column(String(50), default="Received")  # Received, Processing, Replied, Escalated, Ignored

    thread_node = relationship("Thread", back_populates="emails")
    actions = relationship("Action", back_populates="email_node")

    # Index for rapid thread history timeline reconstruction
    __table_args__ = (Index("idx_thread_timeline", "thread_id", "timestamp"),)

class Action(Base):
    __tablename__ = "actions"
    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("emails.id"), nullable=False)
    agent_reasoning_log = Column(JSON, nullable=False)
    action_type = Column(String(100), nullable=False)  # Auto-Reply, Escalate, Legal-Flag, Ticket-Created, Ignored
    proposed_content = Column(Text, nullable=True)
    is_approved = Column(Boolean, default=False)
    approved_by = Column(String(255), nullable=True)
    executed_at = Column(DateTime, nullable=True)

    email_node = relationship("Email", back_populates="actions")

class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"
    id = Column(Integer, primary_key=True, index=True)
    source_doc = Column(String(255), nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding_meta = Column(JSON, nullable=True)  # Metadata pointer (ChromaDB handles true vectors)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class WebIntelligenceCache(Base):
    __tablename__ = "web_intelligence_cache"
    id = Column(Integer, primary_key=True, index=True)
    source_url = Column(String(512), nullable=False)
    target_entity = Column(String(255), nullable=False, index=True)
    scraped_data = Column(JSON, nullable=False)
    scraped_at = Column(DateTime, default=datetime.datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(100), nullable=False)
    action = Column(String(255), nullable=False)
    performed_by = Column(String(255), nullable=False)  # agent or user_id
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    diff = Column(JSON, nullable=True)