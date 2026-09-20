from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():
    return {
        "message": "Support Ticket System V2 API"
    }
