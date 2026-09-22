from fastapi import APIRouter
from app.schemas.ticket import TicketCreate, TicketResponse

router = APIRouter()


@router.post("/tickets", status_code=201, response_model=TicketResponse)
def create_ticket(ticket: TicketCreate):
    return {
        "title": ticket.title,
        "description": ticket.description,
        "category": ticket.category,
        "priority": ticket.priority
    }


@router.get("/tickets/{ticket_id}")
def get_ticket(ticket_id: int):
    return {
        "ticket_id": ticket_id
    }


@router.get("/tickets")
def get_tickets(status: str | None = None):
    return {
        "status_filter": status
    }
