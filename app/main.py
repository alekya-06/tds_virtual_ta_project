from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional # Optional import for image handling if needed in the future

app = FastAPI()
# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

class QuestionRequest(BaseModel):
    question: str
    image: Optional[str] = None

@app.get("/health/")
async def health_check():
    return {"message": "FastAPI is running!"}

@app.post("/")
async def root():
    return {"message": "Virtual TA is running!"}

@app.post("/api/")
async def answer_question(request: QuestionRequest):
    return {
        "question": request.question,
        "answer": "This is a placeholder response. Work in progress!",
        "links": []
    }

