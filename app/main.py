# FastAPI app entry point placeholder
from fastapi import FastAPI

app = FastAPI(title="Agentic Sales System")

@app.get("/")
async def root():
    return {"status": "alive", "message": "Agentic Sales System Gateway"}

# Webhook endpoint will be added here
