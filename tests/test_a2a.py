"""Unit tests for Scrybe A2A Protocol Layer.

Tests for:
- A2A data models (AgentCard, Task, Message, Artifact, TaskState)
- A2A server JSON-RPC dispatch and task lifecycle
- A2A client message creation
- A2A registry agent management
- A2A agent wrappers (Agent Card definitions)
"""

import asyncio
import pytest
from datetime import datetime, timezone

from scrybe.a2a.models import (
    AgentCard,
    AgentCapabilities,
    AgentSkill,
    Artifact,
    DataPart,
    JsonRpcRequest,
    JsonRpcResponse,
    Message,
    Task,
    TaskState,
    TaskStatus,
    TextPart,
)
from scrybe.a2a.registry import AgentRegistry
from scrybe.a2a.client import A2AClient
from scrybe.a2a.server import A2AServer


# ── Test A2A Models ──────────────────────────────────────────────

class TestTaskLifecycle:
    """Tests for A2A Task state machine."""

    def test_task_creation_defaults(self):
        task = Task()
        assert task.task_id.startswith("task_")
        assert task.status.state == TaskState.SUBMITTED
        assert task.messages == []
        assert task.artifacts == []
        assert not task.is_terminal

    def test_task_state_transitions(self):
        task = Task()
        assert task.status.state == TaskState.SUBMITTED

        task.start_work("Processing...")
        assert task.status.state == TaskState.WORKING
        assert task.status.message == "Processing..."
        assert not task.is_terminal

        task.complete("Done!")
        assert task.status.state == TaskState.COMPLETED
        assert task.is_terminal

    def test_task_failure(self):
        task = Task()
        task.start_work()
        task.fail("Something went wrong")
        assert task.status.state == TaskState.FAILED
        assert task.status.message == "Something went wrong"
        assert task.is_terminal

    def test_task_cancellation(self):
        task = Task()
        task.cancel("User requested")
        assert task.status.state == TaskState.CANCELED
        assert task.is_terminal

    def test_task_messages_and_artifacts(self):
        task = Task()
        msg = Message(role="user")
        msg.add_text("Hello")
        task.add_message(msg)

        art = Artifact(name="result")
        art.add_data({"key": "value"})
        task.add_artifact(art)

        assert len(task.messages) == 1
        assert len(task.artifacts) == 1
        assert task.latest_artifact_data == {"key": "value"}


class TestMessage:
    """Tests for A2A Message operations."""

    def test_message_creation(self):
        msg = Message(role="user")
        assert msg.message_id.startswith("msg_")
        assert msg.role == "user"

    def test_message_text_parts(self):
        msg = Message()
        msg.add_text("Hello world")
        assert msg.get_text() == "Hello world"

    def test_message_data_parts(self):
        msg = Message()
        msg.add_data({"price": 5.0, "model": "GPT-4o"})
        data = msg.get_data()
        assert data["price"] == 5.0
        assert data["model"] == "GPT-4o"

    def test_message_mixed_parts(self):
        msg = Message()
        msg.add_text("Extract pricing")
        msg.add_data({"url": "https://openai.com"})
        assert "Extract pricing" in msg.get_text()
        assert msg.get_data()["url"] == "https://openai.com"


class TestArtifact:
    """Tests for A2A Artifact operations."""

    def test_artifact_creation(self):
        art = Artifact(name="test_artifact")
        assert art.artifact_id.startswith("art_")
        assert art.name == "test_artifact"

    def test_artifact_data(self):
        art = Artifact(name="result")
        art.add_data({"records": [{"company": "OpenAI"}]})
        assert art.get_data()["records"][0]["company"] == "OpenAI"


class TestAgentCard:
    """Tests for A2A Agent Card."""

    def test_agent_card_creation(self):
        card = AgentCard(
            name="test_agent",
            description="A test agent",
            url="http://localhost:9000",
            skills=[
                AgentSkill(
                    id="test_skill",
                    name="Test Skill",
                    description="Does testing",
                    tags=["test"],
                ),
            ],
        )
        assert card.name == "test_agent"
        assert card.protocol_version == "a2a/1.0"
        assert len(card.skills) == 1
        assert card.skills[0].id == "test_skill"

    def test_agent_card_serialization(self):
        card = AgentCard(
            name="reader",
            description="Reader Agent",
            url="http://localhost:8011",
        )
        data = card.model_dump(mode="json")
        assert data["name"] == "reader"
        assert data["protocol_version"] == "a2a/1.0"

        # Roundtrip
        card2 = AgentCard(**data)
        assert card2.name == card.name


class TestJsonRpc:
    """Tests for JSON-RPC 2.0 envelope models."""

    def test_request_creation(self):
        req = JsonRpcRequest(
            method="agent/sendMessage",
            params={"task_id": "123"},
        )
        assert req.jsonrpc == "2.0"
        assert req.method == "agent/sendMessage"

    def test_response_creation(self):
        resp = JsonRpcResponse(
            id="abc",
            result={"task_id": "task_123", "status": {"state": "submitted"}},
        )
        assert resp.id == "abc"
        assert resp.result["task_id"] == "task_123"

    def test_error_response(self):
        resp = JsonRpcResponse(
            id="abc",
            error={"code": -32601, "message": "Method not found"},
        )
        assert resp.error["code"] == -32601


# ── Test A2A Registry ────────────────────────────────────────────

class TestAgentRegistry:
    """Tests for A2A agent registry."""

    def test_register_and_get(self):
        registry = AgentRegistry()
        card = AgentCard(
            name="reader",
            description="Reader Agent",
            url="http://localhost:8011",
        )
        registry.register(card)
        assert registry.agent_count == 1

        found = registry.get("reader")
        assert found is not None
        assert found.name == "reader"

    def test_get_url(self):
        registry = AgentRegistry()
        card = AgentCard(name="analyst", description="Analyst", url="http://localhost:8012")
        registry.register(card)
        assert registry.get_url("analyst") == "http://localhost:8012"

    def test_deregister(self):
        registry = AgentRegistry()
        card = AgentCard(name="test", description="Test", url="http://localhost:9000")
        registry.register(card)
        assert registry.agent_count == 1

        registry.deregister("test")
        assert registry.agent_count == 0
        assert registry.get("test") is None

    def test_list_agents(self):
        registry = AgentRegistry()
        registry.register(AgentCard(name="a1", description="Agent 1", url="http://localhost:8001"))
        registry.register(AgentCard(name="a2", description="Agent 2", url="http://localhost:8002"))

        agents = registry.list_agents()
        assert len(agents) == 2
        names = {a["name"] for a in agents}
        assert "a1" in names
        assert "a2" in names

    def test_find_by_skill(self):
        registry = AgentRegistry()
        card = AgentCard(
            name="reader",
            description="Reader",
            url="http://localhost:8011",
            skills=[AgentSkill(id="scrape_sources", name="Scraping", description="Scrapes")],
        )
        registry.register(card)

        found = registry.find_by_skill("scrape_sources")
        assert len(found) == 1
        assert found[0].name == "reader"

        not_found = registry.find_by_skill("nonexistent_skill")
        assert len(not_found) == 0

    def test_health_management(self):
        registry = AgentRegistry()
        card = AgentCard(name="test", description="Test", url="http://localhost:9000")
        registry.register(card)

        assert registry.healthy_count == 1

        registry.mark_unhealthy("test")
        registry.mark_unhealthy("test")
        registry.mark_unhealthy("test")  # 3 failures → unhealthy
        assert registry.healthy_count == 0

        registry.mark_healthy("test")
        assert registry.healthy_count == 1


# ── Test A2A Server ──────────────────────────────────────────────

class TestA2AServer:
    """Tests for the A2A server JSON-RPC dispatch."""

    def _make_server(self):
        async def echo_handler(task: Task) -> Task:
            msg = task.messages[-1] if task.messages else None
            if msg:
                art = Artifact(name="echo")
                art.add_data({"echo": msg.get_text()})
                task.add_artifact(art)
            task.complete("Echo complete")
            return task

        card = AgentCard(
            name="echo_agent",
            description="Echo agent for testing",
            url="http://localhost:9999",
        )
        return A2AServer(agent_card=card, handler=echo_handler)

    def test_agent_card_retrieval(self):
        server = self._make_server()
        card = server.get_agent_card()
        assert card["name"] == "echo_agent"
        assert card["protocol_version"] == "a2a/1.0"

    @pytest.mark.asyncio
    async def test_send_message_creates_task(self):
        server = self._make_server()
        request = {
            "jsonrpc": "2.0",
            "method": "agent/sendMessage",
            "params": {
                "message": {
                    "role": "user",
                    "parts": [{"type": "text", "text": "Hello!"}],
                },
            },
            "id": "test_1",
        }

        response = await server.handle_jsonrpc(request)
        assert response.get("error") is None
        result = response["result"]
        assert "task_id" in result
        assert result["status"]["state"] in ("submitted", "working", "completed")

    @pytest.mark.asyncio
    async def test_method_not_found(self):
        server = self._make_server()
        request = {
            "jsonrpc": "2.0",
            "method": "agent/nonexistent",
            "params": {},
            "id": "test_2",
        }

        response = await server.handle_jsonrpc(request)
        assert response["error"]["code"] == -32601

    @pytest.mark.asyncio
    async def test_get_task_not_found(self):
        server = self._make_server()
        request = {
            "jsonrpc": "2.0",
            "method": "agent/getTask",
            "params": {"task_id": "nonexistent"},
            "id": "test_3",
        }

        response = await server.handle_jsonrpc(request)
        assert response.get("error") is not None

    @pytest.mark.asyncio
    async def test_list_tasks(self):
        server = self._make_server()

        # Send a message to create a task
        send_req = {
            "jsonrpc": "2.0",
            "method": "agent/sendMessage",
            "params": {
                "message": {
                    "role": "user",
                    "parts": [{"type": "text", "text": "Test"}],
                },
            },
            "id": "test_4a",
        }
        await server.handle_jsonrpc(send_req)

        # List tasks
        list_req = {
            "jsonrpc": "2.0",
            "method": "agent/listTasks",
            "params": {},
            "id": "test_4b",
        }
        response = await server.handle_jsonrpc(list_req)
        assert response.get("error") is None
        assert response["result"]["total"] >= 1


# ── Test A2A Client Helpers ──────────────────────────────────────

class TestA2AClientHelpers:
    """Tests for A2A client utility methods."""

    def test_create_message_text(self):
        msg = A2AClient.create_message(text="Hello")
        assert msg.get_text() == "Hello"
        assert msg.role == "user"

    def test_create_message_data(self):
        msg = A2AClient.create_message(data={"key": "value"})
        assert msg.get_data() == {"key": "value"}

    def test_create_message_combined(self):
        msg = A2AClient.create_message(text="Process this", data={"url": "https://example.com"})
        assert "Process this" in msg.get_text()
        assert msg.get_data()["url"] == "https://example.com"

    def test_parse_sse_event(self):
        event_str = "event: task_update\ndata: {\"state\": \"working\"}"
        result = A2AClient._parse_sse_event(event_str)
        assert result["event"] == "task_update"
        assert result["data"]["state"] == "working"


# ── Test A2A Agent Wrappers ──────────────────────────────────────

class TestAgentWrappers:
    """Tests for the A2A agent wrapper card definitions."""

    def test_all_agent_cards_defined(self):
        from scrybe.agents.a2a_wrappers import ALL_AGENT_CARDS
        assert len(ALL_AGENT_CARDS) == 6

        names = {c.name for c in ALL_AGENT_CARDS}
        expected = {"compliance", "reader", "analyst", "memory", "strategist", "formatter"}
        assert names == expected

    def test_agent_cards_have_skills(self):
        from scrybe.agents.a2a_wrappers import ALL_AGENT_CARDS
        for card in ALL_AGENT_CARDS:
            assert len(card.skills) >= 1, f"{card.name} has no skills"
            for skill in card.skills:
                assert skill.id, f"{card.name} skill missing id"
                assert skill.name, f"{card.name} skill missing name"

    def test_agent_cards_protocol_version(self):
        from scrybe.agents.a2a_wrappers import ALL_AGENT_CARDS
        for card in ALL_AGENT_CARDS:
            assert card.protocol_version == "a2a/1.0"

    def test_agent_cards_have_unique_ports(self):
        from scrybe.agents.a2a_wrappers import ALL_AGENT_CARDS
        urls = [c.url for c in ALL_AGENT_CARDS]
        assert len(urls) == len(set(urls)), "Agent URLs must be unique"

    def test_create_all_servers(self):
        from scrybe.agents.a2a_wrappers import create_all_agent_servers
        servers = create_all_agent_servers()
        assert len(servers) == 6
        assert "reader" in servers
        assert "analyst" in servers
