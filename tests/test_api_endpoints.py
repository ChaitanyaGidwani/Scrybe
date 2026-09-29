"""Integration tests for FastAPI endpoints with A2A and SPA static files."""

import pytest
from fastapi.testclient import TestClient

from scrybe.api.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["protocol"] == "a2a/1.0"


def test_list_agents_endpoint(client):
    response = client.get("/api/v1/agents")
    assert response.status_code == 200
    data = response.json()
    assert data["protocol"] == "a2a/1.0"
    assert data["count"] == 6
    agent_names = [a["name"] for a in data["agents"]]
    assert "reader" in agent_names
    assert "analyst" in agent_names
    assert "strategist" in agent_names
    assert "compliance" in agent_names


def test_get_agent_card(client):
    response = client.get("/api/v1/agents/analyst/card")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "analyst"
    assert len(data["skills"]) >= 1


def test_get_agent_card_not_found(client):
    response = client.get("/api/v1/agents/unknown_agent/card")
    assert response.status_code == 404


def test_matrix_endpoint(client):
    response = client.get("/api/v1/matrix")
    assert response.status_code == 200
    data = response.json()
    assert "competitors" in data


def test_reports_endpoint(client):
    response = client.get("/api/v1/reports")
    assert response.status_code == 200
    data = response.json()
    assert "reports" in data


def test_audits_endpoint(client):
    response = client.get("/api/v1/audits")
    assert response.status_code == 200
    data = response.json()
    assert "audits" in data


def test_insights_endpoint(client):
    response = client.get("/api/v1/insights")
    assert response.status_code == 200
    data = response.json()
    assert "insights" in data


def test_progress_history(client):
    response = client.get("/api/v1/a2a/progress")
    assert response.status_code == 200
    data = response.json()
    assert "events" in data


def test_spa_root_serve(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
