from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
'''
app = FastAPI()
# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

class QuestionRequest(BaseModel):
    question: str
    image: str | None = None 

@app.get("/")
async def health_check():
    return {"message": "FastAPI is running!"}

@app.post("/api/")
async def answer_question(request: Request):
    return {
        "answer": "This is a placeholder response. Work in progress!",
        "links": []
    }
'''



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

class QuestionRequest(BaseModel):
    question: str
    image: str | None = None

# Explicit POST handler
@app.post("/api/")
async def answer_question(request: QuestionRequest):
    return {
        "answer": f"Placeholder response to: {request.question}",
        "links": []
    }

# Health check
@app.get("/")
async def root():
    return {"message": "FastAPI is running!"}