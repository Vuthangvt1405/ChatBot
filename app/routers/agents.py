"""Agent Studio API (STORY-01). Errors are mapped in app/errors.py."""

import uuid

from fastapi import APIRouter, Response

from app.schemas import AgentProfileOut, AgentProfileRequest, AgentStudioOptionsOut
from app.services.agent_profiles import AgentProfileServiceDep
from app.workspace import CurrentWorkspaceDep

router = APIRouter(prefix="/api", tags=["Agent Studio"])

_PROBLEM = {"content": {"application/problem+json": {}}}


@router.get(
    "/agents",
    response_model=list[AgentProfileOut],
    summary="Lists the workspace's saved agents, by name.",
    responses={500: _PROBLEM},
)
async def list_agents(
    agents: AgentProfileServiceDep, workspace: CurrentWorkspaceDep
) -> list[AgentProfileOut]:
    return await agents.list_agents(workspace)


@router.post(
    "/agents",
    status_code=201,
    response_model=AgentProfileOut,
    summary="Creates an agent. The page then selects it (AC14).",
    responses={400: _PROBLEM, 409: _PROBLEM, 500: _PROBLEM},
)
async def create_agent(
    body: AgentProfileRequest,
    response: Response,
    agents: AgentProfileServiceDep,
    workspace: CurrentWorkspaceDep,
) -> AgentProfileOut:
    agent = await agents.create_agent(workspace, body)
    response.headers["Location"] = f"/api/agents/{agent.id}"
    return agent


@router.get(
    "/agents/{agent_id}",
    response_model=AgentProfileOut,
    summary="Returns one agent.",
    responses={400: _PROBLEM, 404: _PROBLEM, 500: _PROBLEM},
)
async def get_agent(
    agent_id: uuid.UUID, agents: AgentProfileServiceDep, workspace: CurrentWorkspaceDep
) -> AgentProfileOut:
    return await agents.get_agent(workspace, agent_id)


@router.put(
    "/agents/{agent_id}",
    response_model=AgentProfileOut,
    summary="Replaces an agent's editable fields. The last save wins.",
    responses={400: _PROBLEM, 404: _PROBLEM, 409: _PROBLEM, 500: _PROBLEM},
)
async def update_agent(
    agent_id: uuid.UUID,
    body: AgentProfileRequest,
    agents: AgentProfileServiceDep,
    workspace: CurrentWorkspaceDep,
) -> AgentProfileOut:
    return await agents.update_agent(workspace, agent_id, body)


@router.get(
    "/agent-studio/options",
    response_model=AgentStudioOptionsOut,
    summary="Presets, supported models, tools, thinking levels and limits for the Studio form.",
    responses={500: _PROBLEM},
)
async def get_options(agents: AgentProfileServiceDep) -> AgentStudioOptionsOut:
    return agents.get_options()
