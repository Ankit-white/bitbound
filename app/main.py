from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.agents import router as agent_router

app = FastAPI(title="BitBound Pay API")

app.include_router(auth_router)
app.include_router(agent_router)

@app.get("/")
def root():
    return {"message": "BitBound Pay API is running"}