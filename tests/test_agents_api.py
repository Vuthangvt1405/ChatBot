"""STORY-01 Agent Studio: API, DB and config tests.

Plan: docs/features/plans/ai-data-studio/STORY-01-agent-studio-plan.md §7
Workspaces are switched with app.dependency_overrides[get_current_workspace] (S1).
"""

import json
import logging
import time
import uuid
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import OpenRouterSettings
from app.main import create_app
from app.models import AgentProfile, Base, Conversation, Message
from app.schemas import AGENT_REQUIRED_MESSAGE, AgentProfileRequest
from app.services.agent_presets import PRESETS
from app.services.agent_profiles import get_agent_profile_service
from app.workspace import DEFAULT_WORKSPACE_ID, get_current_workspace
from tests.conftest import make_settings, use_echo_provider

M1 = "stealth/crouton-alpha"  # the default model in make_settings
M2 = "vendor/model-two"
W2 = uuid.UUID(int=2)
REQUIRED = [AGENT_REQUIRED_MESSAGE]
EDITABLE = ("name", "systemPrompt", "modelId", "enabledTools", "thinkingLevel")
AC2_LABELS = [
    "Web Search & Crawl",
    "Corpus EDA & Token Profiling",
    "Synthetic Data Generator",
    "Data Recipe & Code Generator",
]


# ---------- helpers ----------


def body(**overrides) -> dict:
    """The G1 baseline body."""
    data = {
        "name": "DataScout Pro",
        "systemPrompt": "p" * 200,
        "modelId": M1,
        "enabledTools": ["WEB_SEARCH"],
    }
    data.update(overrides)
    return data


def post(client: TestClient, **overrides):
    return client.post("/api/agents", json=body(**overrides))


def create(client: TestClient, **overrides) -> dict:
    response = post(client, **overrides)
    assert response.status_code == 201, response.text
    return response.json()


def put(client: TestClient, agent: dict, **overrides):
    data = {key: agent[key] for key in EDITABLE}
    data.update(overrides)
    return client.put(f"/api/agents/{agent['id']}", json=data)


def get(client: TestClient, agent_id) -> dict:
    response = client.get(f"/api/agents/{agent_id}")
    assert response.status_code == 200, response.text
    return response.json()


def listed(client: TestClient) -> list[dict]:
    response = client.get("/api/agents")
    assert response.status_code == 200, response.text
    return response.json()


def errors_of(response) -> dict[str, list[str]]:
    assert response.status_code == 400, response.text
    assert response.headers["content-type"] == "application/problem+json"
    return response.json()["errors"]


def problem(response, status: int, title: str) -> dict:
    assert response.status_code == status, response.text
    assert response.headers["content-type"] == "application/problem+json"
    payload = response.json()
    assert payload["title"] == title
    return payload


def db_count(client: TestClient, model) -> int:
    async def run() -> int:
        async with client.app.state.sessionmaker() as session:
            return await session.scalar(select(func.count()).select_from(model))

    return client.portal.call(run)


def act_as(app: FastAPI, workspace: uuid.UUID) -> None:
    app.dependency_overrides[get_current_workspace] = lambda: workspace


def act_as_owner(app: FastAPI) -> None:
    app.dependency_overrides.pop(get_current_workspace, None)


def parse(timestamp: str) -> datetime:
    return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))


@pytest.fixture
def two_model_client(tmp_path) -> Iterator[TestClient]:
    """A client whose supported models are [M1, M2]."""
    settings = make_settings(
        tmp_path / "two-models.db",
        openrouter=OpenRouterSettings(api_key="test-key", supported_models=[M1, M2]),
    )
    app = create_app(settings)
    use_echo_provider(app)
    with TestClient(app) as client:
        yield client


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        yield session
    await engine.dispose()


# Group 1 — Creating an agent saves it (covers AC1, AC6, AC7, AC12) · API
# Baseline: Given an empty workspace · When `POST /api/agents` with name "DataScout Pro", a
#   200-char prompt, the default model, `["WEB_SEARCH"]`


def test_ads01_ac1_create_agent_returns_201_and_saved_profile(client: TestClient):
    response = post(client)

    assert response.status_code == 201
    agent = response.json()
    assert response.headers["Location"] == f"/api/agents/{agent['id']}"
    uuid.UUID(agent["id"])
    assert agent["name"] == "DataScout Pro"
    assert agent["systemPrompt"] == "p" * 200
    assert agent["modelId"] == M1
    assert agent["enabledTools"] == ["WEB_SEARCH"]
    assert agent["thinkingLevel"] == "MEDIUM"
    assert "isActive" not in agent


def test_ads01_ac1_create_name_60_chars_returns_201(client: TestClient):
    assert post(client, name="n" * 60).status_code == 201


def test_ads01_ac1_create_prompt_3000_chars_returns_201(client: TestClient):
    assert post(client, systemPrompt="p" * 3000).status_code == 201


def test_ads01_ac1_create_trims_name_and_prompt(client: TestClient):
    agent = create(client, name="  DataScout Pro  ", systemPrompt="\n  Be strict. \n")
    longest = create(client, name=" " + "n" * 60 + " ")

    assert agent["name"] == "DataScout Pro"
    assert agent["systemPrompt"] == "Be strict."
    assert longest["name"] == "n" * 60


def test_ads01_ac1_create_second_agent_keeps_first_unchanged(client: TestClient):
    first = create(client)
    create(client, name="Second")

    agents = listed(client)
    assert len(agents) == 2
    assert next(a for a in agents if a["id"] == first["id"]) == first


def test_ads01_ac1_created_agent_listed_and_fetchable(client: TestClient):
    agent = create(client)

    assert listed(client) == [agent]
    assert get(client, agent["id"]) == agent


def test_ads01_ac1_create_name_61_chars_returns_400_nothing_saved(client: TestClient):
    assert "name" in errors_of(post(client, name="n" * 61))
    assert listed(client) == []


def test_ads01_ac1_create_prompt_3001_chars_returns_400_not_echoed(client: TestClient):
    response = post(client, systemPrompt="q" * 3001)

    assert "systemPrompt" in errors_of(response)
    assert "q" * 100 not in response.text
    assert listed(client) == []


@pytest.mark.parametrize("name", ["Data\nScout", "Data\tScout", "Data\x00Scout"])
def test_ads01_ac1_create_name_with_control_chars_returns_400(client: TestClient, name: str):
    assert "name" in errors_of(post(client, name=name))
    assert listed(client) == []


def test_ads01_ac1_create_duplicate_name_ignoring_case_returns_409(client: TestClient):
    first = create(client)

    response = post(client, name="datascout pro")

    payload = problem(response, 409, "Agent name taken")
    assert payload["detail"] == "An agent with this name already exists."
    assert listed(client) == [first]


def test_ads01_ac1_create_when_50_agents_exist_returns_409_limit(client: TestClient):
    for i in range(50):
        create(client, name=f"Agent {i}")

    response = post(client, name="One too many")

    payload = problem(response, 409, "Agent limit reached")
    assert payload["detail"] == "You can save up to 50 agents."
    assert len(listed(client)) == 50


def test_ads01_ac1_create_malformed_json_returns_400(client: TestClient):
    response = client.post(
        "/api/agents", content="{not json", headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 400
    assert listed(client) == []


def test_ads01_ac1_create_name_wrong_type_returns_400(client: TestClient):
    assert "name" in errors_of(post(client, name=123))
    assert listed(client) == []


# Group 2 — Name and instructions are required (covers AC5) · API
# Baseline: Given an empty workspace · When `POST /api/agents` with a 1-char name and a 1-char
#   prompt (otherwise as G1)


def without(field: str) -> dict:
    data = body(name="A", systemPrompt="B")
    del data[field]
    return data


def test_ads01_ac5_single_char_name_and_prompt_accepted(client: TestClient):
    assert post(client, name="A", systemPrompt="B").status_code == 201


def test_ads01_ac5_empty_name_returns_400_required_message(client: TestClient):
    assert errors_of(post(client, name="", systemPrompt="B"))["name"] == REQUIRED
    assert listed(client) == []


def test_ads01_ac5_whitespace_name_returns_400_required_message(client: TestClient):
    assert errors_of(post(client, name="   ", systemPrompt="B"))["name"] == REQUIRED
    assert listed(client) == []


def test_ads01_ac5_missing_name_returns_400_required_message(client: TestClient):
    response = client.post("/api/agents", json=without("name"))

    assert errors_of(response)["name"] == REQUIRED
    assert listed(client) == []


def test_ads01_ac5_empty_prompt_returns_400_required_message(client: TestClient):
    assert errors_of(post(client, name="A", systemPrompt=""))["systemPrompt"] == REQUIRED
    assert listed(client) == []


def test_ads01_ac5_whitespace_prompt_returns_400_required_message(client: TestClient):
    assert errors_of(post(client, name="A", systemPrompt="\n  \t"))["systemPrompt"] == REQUIRED
    assert listed(client) == []


def test_ads01_ac5_missing_prompt_returns_400_required_message(client: TestClient):
    response = client.post("/api/agents", json=without("systemPrompt"))

    assert errors_of(response)["systemPrompt"] == REQUIRED
    assert listed(client) == []


def test_ads01_ac5_both_empty_returns_400_both_fields_flagged(client: TestClient):
    errors = errors_of(post(client, name="", systemPrompt=""))

    assert errors["name"] == REQUIRED
    assert errors["systemPrompt"] == REQUIRED
    assert listed(client) == []


def test_ads01_ac5_update_with_blank_name_returns_400_profile_unchanged(client: TestClient):
    agent = create(client)

    assert errors_of(put(client, agent, name=""))["name"] == REQUIRED
    assert get(client, agent["id"]) == agent


def test_ads01_ac5_update_with_blank_prompt_returns_400_profile_unchanged(client: TestClient):
    agent = create(client)

    assert errors_of(put(client, agent, systemPrompt="  "))["systemPrompt"] == REQUIRED
    assert get(client, agent["id"]) == agent


# Group 3 — Editing an agent saves it (covers AC1, AC7, AC10, D3) · API
# Baseline: Given agents A and B · When `PUT /api/agents/{B}` with a new name and prompt


@pytest.fixture
def a_and_b(client: TestClient) -> tuple[dict, dict]:
    return create(client, name="A"), create(client, name="Beta")


def test_ads01_ac1_update_agent_saves_new_values(client: TestClient, a_and_b):
    a, b = a_and_b
    time.sleep(0.02)

    response = put(client, b, name="Gamma", systemPrompt="New instructions")

    assert response.status_code == 200, response.text
    updated = response.json()
    assert updated["name"] == "Gamma"
    assert updated["systemPrompt"] == "New instructions"
    assert updated["createdAt"] == b["createdAt"]
    assert parse(updated["updatedAt"]) > parse(b["updatedAt"])
    assert get(client, b["id"]) == updated
    assert get(client, a["id"]) == a


def test_ads01_ac1_update_with_same_values_returns_200_unchanged(client: TestClient, a_and_b):
    _, b = a_and_b

    response = put(client, b)

    assert response.status_code == 200
    assert {k: response.json()[k] for k in EDITABLE} == {k: b[k] for k in EDITABLE}


def test_ads01_ac1_update_changing_case_of_own_name_returns_200(client: TestClient, a_and_b):
    _, b = a_and_b

    response = put(client, b, name="BETA")

    assert response.status_code == 200
    assert response.json()["name"] == "BETA"


def test_ads01_ac1_two_saves_of_same_agent_last_one_wins(client: TestClient, a_and_b):
    _, b = a_and_b

    assert put(client, b, systemPrompt="First edit").status_code == 200
    assert put(client, b, systemPrompt="Second edit").status_code == 200

    assert get(client, b["id"])["systemPrompt"] == "Second edit"


def test_ads01_ac1_update_unknown_agent_returns_404(client: TestClient, a_and_b):
    before = listed(client)

    response = client.put(f"/api/agents/{uuid.uuid4()}", json=body())

    problem(response, 404, "Agent not found")
    assert listed(client) == before
    assert len(before) == 2


def test_ads01_ac1_update_malformed_id_returns_400(client: TestClient, a_and_b):
    before = listed(client)

    assert client.put("/api/agents/not-a-uuid", json=body()).status_code == 400
    assert listed(client) == before


def test_ads01_ac1_update_to_other_agents_name_returns_409_unchanged(client: TestClient, a_and_b):
    _, b = a_and_b

    problem(put(client, b, name="a"), 409, "Agent name taken")
    assert get(client, b["id"]) == b


def test_ads01_ac1_get_unknown_agent_returns_404(client: TestClient):
    problem(client.get(f"/api/agents/{uuid.uuid4()}"), 404, "Agent not found")


# Group 4 — Tool switches are saved as a valid toolset (covers AC2, AC8) · API
# Baseline: Given an agent with `["WEB_SEARCH"]` · When `PUT` with `enabledTools: ["WEB_SEARCH",
#   "CORPUS_EDA"]`


def assert_tools_unchanged(client: TestClient, agent: dict) -> None:
    assert get(client, agent["id"])["enabledTools"] == ["WEB_SEARCH"]


def test_ads01_ac2_update_tools_saves_new_toolset(client: TestClient):
    agent = create(client)

    response = put(client, agent, enabledTools=["WEB_SEARCH", "CORPUS_EDA"])

    assert response.status_code == 200
    assert response.json()["enabledTools"] == ["WEB_SEARCH", "CORPUS_EDA"]
    assert get(client, agent["id"])["enabledTools"] == ["WEB_SEARCH", "CORPUS_EDA"]


def test_ads01_ac2_all_four_tools_enabled(client: TestClient):
    agent = create(client)
    every = ["WEB_SEARCH", "CORPUS_EDA", "SYNTHESIZER", "RECIPE_BUILDER"]

    assert put(client, agent, enabledTools=every).json()["enabledTools"] == every


def test_ads01_ac2_empty_toolset_disables_all_tools(client: TestClient):
    agent = create(client)

    assert put(client, agent, enabledTools=[]).json()["enabledTools"] == []


def test_ads01_ac2_tools_returned_in_canonical_order(client: TestClient):
    agent = create(client)

    response = put(client, agent, enabledTools=["RECIPE_BUILDER", "WEB_SEARCH"])

    assert response.json()["enabledTools"] == ["WEB_SEARCH", "RECIPE_BUILDER"]


def test_ads01_ac2_unknown_tool_returns_400_unchanged(client: TestClient):
    agent = create(client)

    assert "enabledTools.0" in errors_of(put(client, agent, enabledTools=["SHELL_EXEC"]))
    assert_tools_unchanged(client, agent)


def test_ads01_ac2_duplicate_tool_returns_400(client: TestClient):
    agent = create(client)

    errors = errors_of(put(client, agent, enabledTools=["WEB_SEARCH", "WEB_SEARCH"]))

    assert errors["enabledTools"] == ["Each tool can only be listed once."]
    assert_tools_unchanged(client, agent)


def test_ads01_ac2_lowercase_tool_returns_400(client: TestClient):
    agent = create(client)

    errors_of(put(client, agent, enabledTools=["web_search"]))
    assert_tools_unchanged(client, agent)


def test_ads01_ac2_null_tools_returns_400(client: TestClient):
    agent = create(client)

    assert "enabledTools" in errors_of(put(client, agent, enabledTools=None))
    assert_tools_unchanged(client, agent)


def test_ads01_ac2_tools_not_a_list_returns_400(client: TestClient):
    agent = create(client)

    assert "enabledTools" in errors_of(put(client, agent, enabledTools="WEB_SEARCH"))
    assert_tools_unchanged(client, agent)


# Group 5 — Studio options: presets, models, tools (covers AC2, AC3, AC4) · API + config unit
# Baseline: Given default settings · When `GET /api/agent-studio/options`


def options(client: TestClient) -> dict:
    response = client.get("/api/agent-studio/options")
    assert response.status_code == 200, response.text
    return response.json()


def test_ads01_ac3_options_lists_three_presets(client: TestClient):
    presets = options(client)["presets"]

    assert [p["title"] for p in presets] == [
        "Strict Technical Evaluator",
        "Domain Data Curator",
        "Red-Team Adversary",
    ]
    assert [p["id"] for p in presets] == [
        "strict-technical-evaluator",
        "domain-data-curator",
        "red-team-adversary",
    ]
    assert all(p["systemPrompt"] for p in presets)


def test_ads01_ac3_every_preset_passes_agent_validation():
    for preset in PRESETS:
        request = AgentProfileRequest(
            name=preset.title, system_prompt=preset.system_prompt, model_id=M1, enabled_tools=[]
        )
        assert request.system_prompt == preset.system_prompt
        assert len(preset.system_prompt) <= 3000


def test_ads01_ac4_options_lists_supported_models_with_default(two_model_client: TestClient):
    result = options(two_model_client)

    assert [m["id"] for m in result["models"]] == [M1, M2]
    assert result["defaultModelId"] == M1


def test_ads01_ac2_options_lists_four_tools_with_labels(client: TestClient):
    tools = options(client)["tools"]

    assert [t["id"] for t in tools] == ["WEB_SEARCH", "CORPUS_EDA", "SYNTHESIZER", "RECIPE_BUILDER"]
    assert [t["label"] for t in tools] == AC2_LABELS


def test_ads01_ac4_default_model_missing_from_list_is_added():
    settings = OpenRouterSettings(api_key="k", model=M1, supported_models=[M2])

    assert settings.supported_models == [M1, M2]


def test_ads01_ac4_blank_supported_model_entry_rejected_at_startup():
    with pytest.raises(ValidationError, match="blank"):
        OpenRouterSettings(api_key="k", model=M1, supported_models=[M1, "  "])


# Group 6 — Chat uses the selected agent's model and instructions (covers AC4, AC8, AC10, AC11,
#   AC14) · unit (`test_openrouter.py`, respx) + API
# Baseline: Given a saved agent B with model M2 and prompt P, supported [M1, M2], default M1 ·
#   When a chat message with `agentId: B` is sent


def test_ads01_ac4_create_with_unsupported_model_returns_400_nothing_saved(client: TestClient):
    errors = errors_of(post(client, modelId="vendor/unlisted"))

    assert errors == {"modelId": ["Choose a supported model."]}
    assert listed(client) == []


def test_ads01_ac4_create_with_empty_model_returns_400(client: TestClient):
    assert "modelId" in errors_of(post(client, modelId=""))
    assert listed(client) == []


def test_ads01_ac4_update_with_unsupported_model_returns_400_unchanged(
    two_model_client: TestClient,
):
    agent = create(two_model_client, modelId=M2)

    assert "modelId" in errors_of(put(two_model_client, agent, modelId="vendor/unlisted"))
    assert get(two_model_client, agent["id"])["modelId"] == M2


def test_ads01_ac10_chat_with_unknown_agent_returns_404_nothing_saved(client: TestClient):
    response = client.post("/api/chat", json={"message": "Hello", "agentId": str(uuid.uuid4())})

    problem(response, 404, "Agent not found")
    assert db_count(client, Conversation) == 0
    assert db_count(client, Message) == 0


def test_ads01_ac10_chat_with_malformed_agent_id_returns_400(client: TestClient):
    response = client.post("/api/chat", json={"message": "Hello", "agentId": "abc"})

    assert "agentId" in errors_of(response)
    assert db_count(client, Conversation) == 0


# Group 9 — Thinking level is saved and sent with every reply (covers AC13, SEC5, SEC6) · API +
#   unit (`test_openrouter.py`, respx)
# Baseline: Given an empty workspace · When `POST /api/agents` (as G1) with `thinkingLevel:
#   "HIGH"`, then a chat message is sent


def test_ads01_ac13_create_with_high_thinking_level_saves_it(client: TestClient):
    agent = create(client, thinkingLevel="HIGH")

    assert agent["thinkingLevel"] == "HIGH"
    assert get(client, agent["id"])["thinkingLevel"] == "HIGH"


def test_ads01_ac13_thinking_level_absent_defaults_to_medium(client: TestClient):
    assert create(client)["thinkingLevel"] == "MEDIUM"


def test_ads01_ac13_options_list_three_thinking_levels(client: TestClient):
    result = options(client)

    assert [t["id"] for t in result["thinkingLevels"]] == ["LOW", "MEDIUM", "HIGH"]
    assert [t["label"] for t in result["thinkingLevels"]] == ["Low", "Medium", "High"]
    assert result["defaultThinkingLevel"] == "MEDIUM"


def test_ads01_ac13_unknown_thinking_level_returns_400_nothing_saved(client: TestClient):
    assert "thinkingLevel" in errors_of(post(client, thinkingLevel="EXTREME"))
    assert listed(client) == []


def test_ads01_ac13_lowercase_thinking_level_returns_400(client: TestClient):
    assert "thinkingLevel" in errors_of(post(client, thinkingLevel="high"))
    assert listed(client) == []


def test_ads01_ac13_null_thinking_level_returns_400(client: TestClient):
    assert "thinkingLevel" in errors_of(post(client, thinkingLevel=None))
    assert listed(client) == []


def test_ads01_ac13_update_with_invalid_level_returns_400_unchanged(client: TestClient):
    agent = create(client, thinkingLevel="HIGH")

    assert "thinkingLevel" in errors_of(put(client, agent, thinkingLevel="MAX"))
    assert get(client, agent["id"])["thinkingLevel"] == "HIGH"


# Group S1 — Workspaces stay separate (covers SEC1, SEC2, SEC3, AC10) · API (dependency override
#   for workspace)
# Baseline: Given agent A created in workspace W1 · When a request is made as W1 or W2


def test_ads01_sec1_owner_workspace_can_read_its_agent(app: FastAPI, client: TestClient):
    agent = create(client)

    assert get(client, agent["id"]) == agent


def test_ads01_sec1_same_name_allowed_in_other_workspace(app: FastAPI, client: TestClient):
    create(client)
    act_as(app, W2)

    assert post(client).status_code == 201


def test_ads01_sec1_other_workspace_get_returns_same_404_as_unknown(
    app: FastAPI, client: TestClient
):
    agent = create(client)
    act_as(app, W2)

    foreign = client.get(f"/api/agents/{agent['id']}")
    unknown = client.get(f"/api/agents/{uuid.uuid4()}")

    problem(foreign, 404, "Agent not found")
    assert foreign.content == unknown.content


def test_ads01_sec1_other_workspace_update_returns_404_unchanged(app: FastAPI, client: TestClient):
    agent = create(client)
    act_as(app, W2)

    problem(put(client, agent, name="Hijacked"), 404, "Agent not found")
    act_as_owner(app)
    assert get(client, agent["id"]) == agent


def test_ads01_sec1_other_workspace_list_excludes_agent(app: FastAPI, client: TestClient):
    create(client)
    act_as(app, W2)

    assert listed(client) == []


def test_ads01_sec1_other_workspace_chat_with_agent_id_returns_404(
    app: FastAPI, client: TestClient
):
    agent = create(client)
    act_as(app, W2)

    foreign = client.post("/api/chat", json={"message": "Hi", "agentId": agent["id"]})
    unknown = client.post("/api/chat", json={"message": "Hi", "agentId": str(uuid.uuid4())})

    problem(foreign, 404, "Agent not found")
    assert foreign.content == unknown.content
    assert db_count(client, Conversation) == 0


def test_ads01_sec1_other_workspace_ui_send_with_agent_id_returns_404(
    app: FastAPI, client: TestClient
):
    agent = create(client)
    act_as(app, W2)

    response = client.post("/ui/send", data={"message": "Hi", "agent_id": agent["id"]})

    assert response.status_code == 404
    assert response.headers["X-Error-Code"] == "agent_not_found"
    assert response.text == ""
    assert db_count(client, Conversation) == 0


# Group S2 — Server-owned fields can't be set by the client (covers SEC4) · API
# Baseline: Given an empty workspace (W1) · When `POST`/`PUT` with a valid body plus one
#   server-owned field


def test_ads01_sec2_create_ignores_workspace_id(client: TestClient):
    agent = create(client, workspaceId=str(W2))

    assert listed(client) == [agent]
    act_as(client.app, W2)
    assert listed(client) == []


def test_ads01_sec2_create_ignores_client_id(client: TestClient):
    chosen = uuid.uuid4()

    agent = create(client, id=str(chosen))

    assert agent["id"] != str(chosen)


def test_ads01_sec2_create_ignores_timestamps(client: TestClient):
    agent = create(client, createdAt="2000-01-01T00:00:00Z", updatedAt="2000-01-01T00:00:00Z")

    now = datetime.now(UTC)
    for field in ("createdAt", "updatedAt"):
        assert abs(parse(agent[field]) - now) < timedelta(minutes=1)


def test_ads01_sec2_update_ignores_workspace_id(client: TestClient):
    agent = create(client)

    assert put(client, agent, workspaceId=str(W2)).status_code == 200

    assert [a["id"] for a in listed(client)] == [agent["id"]]
    act_as(client.app, W2)
    assert listed(client) == []


# Group S3 — No data leaks (covers SEC5, SEC10) · API
# Baseline: none shared (each test sets up its own probe); negatives only.


def test_ads01_sec3_responses_never_include_workspace_or_name_key(client: TestClient):
    agent = create(client)
    responses = [
        client.get("/api/agents").json()[0],
        get(client, agent["id"]),
        put(client, agent, name="Renamed").json(),
        agent,
    ]

    for payload in responses:
        assert "workspaceId" not in payload
        assert "nameKey" not in payload


def test_ads01_sec3_validation_error_does_not_echo_prompt(client: TestClient):
    marker = "LEAK-MARKER-"
    response = post(client, systemPrompt=marker + "x" * 3000)

    assert response.status_code == 400
    assert marker not in response.text


def test_ads01_sec3_logs_never_contain_system_prompt(
    client: TestClient, caplog: pytest.LogCaptureFixture
):
    caplog.set_level(logging.INFO)
    marker = "SECRET-INSTRUCTIONS-MARKER"

    agent = create(client, systemPrompt=f"{marker} create")
    put(client, agent, systemPrompt=f"{marker} update")
    chat = client.post("/api/chat", json={"message": "Hi", "agentId": agent["id"]})

    assert chat.status_code == 200
    assert marker not in caplog.text
    assert f"Agent {agent['id']} saved in workspace" in caplog.text


def test_ads01_sec3_unexpected_error_returns_fixed_500(app: FastAPI, client: TestClient):
    class Broken:
        async def list_agents(self, workspace_id):
            raise RuntimeError("secret-detail")

    app.dependency_overrides[get_agent_profile_service] = lambda: Broken()

    response = client.get("/api/agents")

    payload = problem(response, 500, "Unexpected error")
    assert payload["detail"] == "Something went wrong. Please try again."
    assert "secret-detail" not in response.text
    assert "Traceback" not in response.text


def test_ads01_sec3_not_found_body_has_no_id(client: TestClient):
    agent_id = uuid.uuid4()

    response = client.get(f"/api/agents/{agent_id}")

    assert response.status_code == 404
    assert str(agent_id) not in response.text


# Group S4 — Injection and abuse (covers SEC6, SEC7, SEC11) · API / page / e2e
# Baseline: none shared; negatives only.


def test_ads01_sec4_sql_like_name_stored_literally(client: TestClient):
    name = "'; DROP TABLE agent_profiles;--"

    agent = create(client, name=name)

    assert agent["name"] == name
    assert [a["name"] for a in listed(client)] == [name]


@pytest.mark.parametrize("model_id", ["../../admin", f"{M1} ", f"{M1}\n", "x" * 300])
def test_ads01_sec4_model_id_injection_strings_rejected(client: TestClient, model_id: str):
    assert "modelId" in errors_of(post(client, modelId=model_id))
    assert listed(client) == []


def test_ads01_sec4_oversized_body_rejected_without_echo(client: TestClient):
    marker = "HUGE-BODY-MARKER"

    response = post(client, systemPrompt=marker + "x" * 1_000_000)

    assert response.status_code == 400
    assert len(response.content) < 2000
    assert marker not in response.text
    assert listed(client) == []


def test_ads01_sec4_non_json_body_rejected(client: TestClient):
    response = client.post(
        "/api/agents", content=json.dumps(body()), headers={"Content-Type": "text/plain"}
    )

    assert response.status_code == 400
    assert listed(client) == []


# Group S5 — Integrity under races (covers SEC9) · integration (real SQLite)
# Baseline: Given a workspace · When agents are written straight to the DB


def profile_row(name_key: str) -> AgentProfile:
    return AgentProfile(
        workspace_id=DEFAULT_WORKSPACE_ID,
        name=name_key,
        name_key=name_key,
        system_prompt="p",
        model_id=M1,
    )


async def test_ads01_sec5_db_accepts_distinct_names_in_workspace(db_session: AsyncSession):
    db_session.add_all([profile_row("alpha"), profile_row("beta")])
    await db_session.commit()

    assert await db_session.scalar(select(func.count()).select_from(AgentProfile)) == 2


async def test_ads01_sec5_db_rejects_duplicate_name_key_in_workspace(db_session: AsyncSession):
    db_session.add(profile_row("alpha"))
    await db_session.commit()

    db_session.add(profile_row("alpha"))
    with pytest.raises(IntegrityError):
        await db_session.commit()


def test_ads01_sec5_unique_violation_on_commit_maps_to_409(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
):
    original = AsyncSession.commit
    failures = [IntegrityError("INSERT", {}, Exception("UNIQUE constraint failed"))]

    async def lost_race(self):
        if failures:
            raise failures.pop()
        return await original(self)

    monkeypatch.setattr(AsyncSession, "commit", lost_race)

    problem(post(client), 409, "Agent name taken")
    assert listed(client) == []
    assert post(client).status_code == 201
