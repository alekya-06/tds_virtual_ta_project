from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import pydantic
from fastapi import Request

app = FastAPI()
# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

@app.get("/")
async def root():
    return {"message": "FastAPI is running!"}

@app.post("/api/")
async def answer_question(request: Request):
    return {
        "answer": "This is a placeholder response. Work in progress!",
        "links": []
    }