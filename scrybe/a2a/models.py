"""A2A Protocol Data Models for Scrybe.

Implements the core primitives of the Agent-to-Agent (A2A) protocol v1.0:
- AgentCard: Agent identity, capabilities, and endpoint discovery
- Task: Stateful unit of work with lifecycle management
- Message: Interaction input between agents
- Artifact: Structured output produced by task execution
- Part: Content container (text, data, file) within messages/artifacts

Based on the A2A v1.0 specification (JSON-RPC 2.0 over HTTP).
See: https://a2a-protocol.org
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional, Union

from pydantic import BaseModel, Field


# ── Task State Machine ──────────────────────────────────────────

class TaskState(str, Enum):
    """A2A Task lifecycle states.

    State transitions:
        SUBMITTED → WORKING → COMPLETED
                            → FAILED
                  → INPUT_REQUIRED → WORKING (after input received)
                  → CANCELED
    """
    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input-required"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


# ── Content Parts ────────────────────────────────────────────────

class TextPart(BaseModel):
    """Plain text content part."""
    type: str = "text"
    text: str


class DataPart(BaseModel):
    """Structured data content part (JSON-serializable)."""
    type: str = "data"
    data: Dict[str, Any]
    mime_type: str = "application/json"


class FilePart(BaseModel):
    """File reference content part."""
    type: str = "file"
    file_uri: str
    mime_type: str = "application/octet-stream"
    name: Optional[str] = None


Part = Union[TextPart, DataPart, FilePart]


# ── Messages & Artifacts ────────────────────────────────────────

class Message(BaseModel):
    """A2A Message — interaction input sent to an agent.

    Messages are the inputs to a task. They carry content parts
    and metadata about the sender.
    """
    message_id: str = Field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:12]}")
    role: str = Field(default="user", description="Sender role: 'user' or 'agent'")
    parts: List[Part] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def add_text(self, text: str) -> "Message":
        """Add a text part to this message."""
        self.parts.append(TextPart(text=text))
        return self

    def add_data(self, data: Dict[str, Any], mime_type: str = "application/json") -> "Message":
        """Add a structured data part to this message."""
        self.parts.append(DataPart(data=data, mime_type=mime_type))
        return self

    def get_text(self) -> str:
        """Extract concatenated text from all text parts."""
        return "\n".join(p.text for p in self.parts if isinstance(p, TextPart))

    def get_data(self) -> Optional[Dict[str, Any]]:
        """Extract data from the first data part."""
        for p in self.parts:
            if isinstance(p, DataPart):
                return p.data
        return None


class Artifact(BaseModel):
    """A2A Artifact — structured output produced by task execution.

    Artifacts are the durable outputs of a completed task.
    """
    artifact_id: str = Field(default_factory=lambda: f"art_{uuid.uuid4().hex[:12]}")
    name: str = ""
    description: str = ""
    parts: List[Part] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def add_text(self, text: str) -> "Artifact":
        """Add a text part to this artifact."""
        self.parts.append(TextPart(text=text))
        return self

    def add_data(self, data: Dict[str, Any]) -> "Artifact":
        """Add a structured data part to this artifact."""
        self.parts.append(DataPart(data=data))
        return self

    def get_data(self) -> Optional[Dict[str, Any]]:
        """Extract data from the first data part."""
        for p in self.parts:
            if isinstance(p, DataPart):
                return p.data
        return None


# ── Task ─────────────────────────────────────────────────────────

class TaskStatus(BaseModel):
    """Current status of a task with optional detail message."""
    state: TaskState = TaskState.SUBMITTED
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Task(BaseModel):
    """A2A Task — the fundamental unit of work.

    Tasks are stateful, identified by a unique ID, and progress
    through the TaskState lifecycle. They accumulate messages (inputs)
    and artifacts (outputs).
    """
    task_id: str = Field(default_factory=lambda: f"task_{uuid.uuid4().hex[:12]}")
    status: TaskStatus = Field(default_factory=TaskStatus)
    messages: List[Message] = Field(default_factory=list)
    artifacts: List[Artifact] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def add_message(self, message: Message) -> "Task":
        """Append an input message."""
        self.messages.append(message)
        self.updated_at = datetime.now(timezone.utc)
        return self

    def add_artifact(self, artifact: Artifact) -> "Task":
        """Append an output artifact."""
        self.artifacts.append(artifact)
        self.updated_at = datetime.now(timezone.utc)
        return self

    def set_state(self, state: TaskState, message: Optional[str] = None) -> "Task":
        """Transition to a new state."""
        self.status = TaskStatus(state=state, message=message)
        self.updated_at = datetime.now(timezone.utc)
        return self

    def start_work(self, message: Optional[str] = None) -> "Task":
        """Transition to WORKING state."""
        return self.set_state(TaskState.WORKING, message or "Processing...")

    def complete(self, message: Optional[str] = None) -> "Task":
        """Transition to COMPLETED state."""
        return self.set_state(TaskState.COMPLETED, message or "Task completed successfully.")

    def fail(self, error: str) -> "Task":
        """Transition to FAILED state."""
        return self.set_state(TaskState.FAILED, error)

    def cancel(self, reason: Optional[str] = None) -> "Task":
        """Transition to CANCELED state."""
        return self.set_state(TaskState.CANCELED, reason or "Canceled by user.")

    @property
    def is_terminal(self) -> bool:
        """Check if the task is in a terminal state."""
        return self.status.state in (TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELED)

    @property
    def latest_artifact_data(self) -> Optional[Dict[str, Any]]:
        """Get data from the most recent artifact."""
        if self.artifacts:
            return self.artifacts[-1].get_data()
        return None


# ── Agent Card (Discovery) ───────────────────────────────────────

class AgentSkill(BaseModel):
    """A specific capability or skill an agent can perform."""
    id: str
    name: str
    description: str
    tags: List[str] = Field(default_factory=list)
    examples: List[str] = Field(default_factory=list)


class AgentCapabilities(BaseModel):
    """Declared capabilities of an A2A agent."""
    streaming: bool = False
    push_notifications: bool = False
    state_transition_history: bool = True


class AgentCard(BaseModel):
    """A2A Agent Card — the agent's identity and discovery metadata.

    Typically served at `/.well-known/agent-card.json`.
    Enables runtime discovery of agent capabilities, endpoint URL,
    and supported interaction patterns.
    """
    name: str
    description: str
    url: str = Field(description="Base HTTP endpoint for this agent")
    version: str = "1.0.0"
    protocol_version: str = "a2a/1.0"
    capabilities: AgentCapabilities = Field(default_factory=AgentCapabilities)
    skills: List[AgentSkill] = Field(default_factory=list)
    default_input_modes: List[str] = Field(default_factory=lambda: ["application/json"])
    default_output_modes: List[str] = Field(default_factory=lambda: ["application/json"])
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ── JSON-RPC 2.0 Envelope ───────────────────────────────────────

class JsonRpcRequest(BaseModel):
    """JSON-RPC 2.0 request envelope."""
    jsonrpc: str = "2.0"
    method: str
    params: Dict[str, Any] = Field(default_factory=dict)
    id: Optional[str] = Field(default_factory=lambda: uuid.uuid4().hex[:12])


class JsonRpcResponse(BaseModel):
    """JSON-RPC 2.0 response envelope."""
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[str] = None


class JsonRpcError(BaseModel):
    """JSON-RPC 2.0 error object."""
    code: int
    message: str
    data: Optional[Any] = None

    # Standard A2A error codes
    PARSE_ERROR: ClassVar[int] = -32700
    INVALID_REQUEST: ClassVar[int] = -32600
    METHOD_NOT_FOUND: ClassVar[int] = -32601
    INVALID_PARAMS: ClassVar[int] = -32602
    INTERNAL_ERROR: ClassVar[int] = -32603
    TASK_NOT_FOUND: ClassVar[int] = -32001
    TASK_ALREADY_COMPLETE: ClassVar[int] = -32002
    AGENT_BUSY: ClassVar[int] = -32003
