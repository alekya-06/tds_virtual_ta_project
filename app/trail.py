from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI()

# CORS configuration (POST-only)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST"],  # Only allow POST requests
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str
    image: Optional[str] = None

# Health check (GET allowed only here)
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Reject GET at root
@app.get("/", include_in_schema=False)
async def reject_root_get():
    raise HTTPException(status_code=405, detail="Method Not Allowed - POST only")

# Main API endpoint (POST only)
@app.post("/")
async def handle_post(request: QuestionRequest):
    return {
        "question": request.question,
        "answer": "This is a placeholder response",
        "links": []
    }

@app.post("/api/")
async def api_endpoint(request: QuestionRequest):
    return {
        "question": request.question,
        "answer": "API endpoint response",
        "links": []
    }