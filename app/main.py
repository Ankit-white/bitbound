from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.agents import router as agent_router
from app.api.wallets import router as wallet_router
from app.api.usages import router as usage_router
from app.api.workflows import router as workflow_router
from app.api.workflow_executions import router as workflow_execution_router
from app.api.payments import router as payment_router
from app.api.credit_packages import router as credit_package_router
from app.api.api_key import router as api_key_router
from app.api.webhooks import router as webhook_router

app = FastAPI(
    title="BitBound Pay API",
    version="1.0.0"
)

app.include_router(auth_router)
app.include_router(agent_router)
app.include_router(wallet_router)
app.include_router(usage_router)
app.include_router(workflow_router)
app.include_router(workflow_execution_router)
app.include_router(payment_router)
app.include_router(credit_package_router)
app.include_router(api_key_router)
app.include_router(webhook_router)

@app.get("/")
def root():
    return {
        "message": "BitBound Pay API is running"
    }