from typing import Dict, Any, List, TypedDict

class AgentState(TypedDict):
    email_id: int
    thread_id: str
    sender: str
    body: str
    history: List[Dict[str, str]]
    category: str
    urgency: str
    requires_human: bool
    suggested_reply: str
    reasoning_steps: List[Dict[str, Any]]
    tool_counter: int
    dry_run: bool