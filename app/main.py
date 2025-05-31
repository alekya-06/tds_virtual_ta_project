from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


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
    image: None 

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
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class TestRequest(BaseModel):
    test_data: str  # Add expected request fields

@app.post("/")
async def test_post(request: TestRequest):  # Use proper request model
    print(f"Received: {request.test_data}")
    return {"message": "POST endpoint is working!", "received": request.test_data}

@app.get("/")
async def test_get():
    return {"message": "GET endpoint is working!"}'''
