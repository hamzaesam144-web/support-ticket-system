from fastapi import FastAPI
from app.api.routes.health import router as health_router
from app.api.routes.tickets import router as tickets_router


app = FastAPI()


app.include_router(health_router)
app.include_router(tickets_router)


@app.get("/")
def root():
    return {
        "message": "Support Ticket System V2 API"
    }
