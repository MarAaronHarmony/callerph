"""API routes for call logs and client management."""

from fastapi import APIRouter, Query
from sqlmodel import Session, col, func, select

from app.db.database import get_engine
from app.models.call_log import CallLog
from app.models.client import Client

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/calls")
async def list_calls(
    client_id: int | None = Query(default=None, description="Filter by client ID"),
    limit: int = Query(default=20, ge=1, le=100, description="Number of results"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
):
    """List call logs with optional filtering and pagination."""
    with Session(get_engine()) as session:
        # Build query
        query = select(CallLog)
        count_query = select(func.count()).select_from(CallLog)

        if client_id is not None:
            query = query.where(CallLog.client_id == client_id)
            count_query = count_query.where(CallLog.client_id == client_id)

        # Get total count
        total = session.exec(count_query).one()

        # Get paginated results
        results = session.exec(
            query.order_by(col(CallLog.started_at).desc()).offset(offset).limit(limit)
        ).all()

        # Enrich with client names
        client_cache: dict[int, str] = {}
        calls = []
        for call in results:
            if call.client_id not in client_cache:
                client = session.get(Client, call.client_id)
                client_cache[call.client_id] = client.name if client else "Unknown"

            calls.append(
                {
                    "id": call.id,
                    "client_name": client_cache[call.client_id],
                    "caller_number": call.caller_number,
                    "started_at": call.started_at.isoformat() if call.started_at else None,
                    "ended_at": call.ended_at.isoformat() if call.ended_at else None,
                    "duration_seconds": call.duration_seconds,
                    "caller_name": call.caller_name,
                    "caller_inquiry": call.caller_inquiry,
                    "conversation_summary": call.conversation_summary,
                    "status": call.status,
                }
            )

        return {"calls": calls, "total": total}


@router.get("/clients")
async def list_clients():
    """List all registered clients."""
    with Session(get_engine()) as session:
        clients = session.exec(select(Client)).all()
        return {
            "clients": [
                {
                    "id": c.id,
                    "name": c.name,
                    "phone_number": c.phone_number,
                    "prompt_file": c.prompt_file,
                    "is_active": c.is_active,
                }
                for c in clients
            ]
        }
