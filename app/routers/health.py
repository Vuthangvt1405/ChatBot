from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_class=PlainTextResponse)
async def health() -> str:
    return "Healthy"
