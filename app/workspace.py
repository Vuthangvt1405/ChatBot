"""The current workspace (STORY-01 SEC1, plan D6).

The app runs locally for one user, so there is no sign-in. Agents still belong to a workspace
so workspaces stay separate. Today there is one default workspace; when picking or creating
workspaces arrives (its own story, plan D15), only get_current_workspace changes.
"""

import uuid
from typing import Annotated

from fastapi import Depends

DEFAULT_WORKSPACE_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def get_current_workspace() -> uuid.UUID:
    """The workspace every agent query is limited to. Tests override it to act as another."""
    return DEFAULT_WORKSPACE_ID


CurrentWorkspaceDep = Annotated[uuid.UUID, Depends(get_current_workspace)]
