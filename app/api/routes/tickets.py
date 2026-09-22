from fastapi import APIRouter, HTTPException
from app.schemas.ticket import TicketCreate, TicketResponse

router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"]
)


@router.post("", status_code=201, response_model=TicketResponse)
def create_ticket(ticket: TicketCreate):
    return {
        "title": ticket.title,
        "description": ticket.description,
        "category": ticket.category,
        "priority": ticket.priority
    }


@router.get("/{ticket_id}")
def get_ticket(ticket_id: int):

    if ticket_id == 999:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    return {
        "ticket_id": ticket_id
    }


@router.get("")
def get_tickets(status: str | None = None):
    return {
        "status_filter": status
    }
