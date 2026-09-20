from fastapi import FastAPI

from app.api.routes.health import router as health_router


app = FastAPI()


app.include_router(health_router)


@app.get("/")
def root():
    return {
        "message": "Support Ticket System V2 API"
    }
