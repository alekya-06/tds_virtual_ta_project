from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import  CORSMiddleware
from pydantic import BaseModel, Field, field_validator, StringConstraints
from typing import Optional, Annotated
import time
from datetime import datetime
from fuzzywuzzy import fuzz
import os
import logging
from .scraper import get_discourse_posts, get_docsify_content
from .image_utils import extract_text_from_image
from .storage import KnowledgeStorage
from .ai_usage import ai_proxy

logger = logging.getLogger(__name__)

# Verify API key from header
async def verify_api_key(api_key: str = Header(default=None)):
    if api_key != os.getenv("API_KEY"):
        raise HTTPException(status_code=403, detail="Invalid API key")

class SystemMetrics:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
     
    def _initialize(self):
        self.metrics = {
            'api_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'request_times': [],
            'image_processing_times': [],
            'last_updated': datetime.now().isoformat(),
            'ai_requests': 0,
            'ai_cost_estimate': 0.0,
            'ai_failures': 0
        }

    @classmethod
    def record_ai_usage(cls, cost: float):
        instance = cls()
        instance.metrics['ai_requests'] += 1
        instance.metrics['ai_cost_estimate'] += cost
    
    @classmethod
    def collect(cls):
        instance = cls()
        request_times = [r['duration'] for r in instance.metrics['request_times']]
        image_times = [r['duration'] for r in instance.metrics['image_processing_times']]
        
        return {
            'total_requests': instance.metrics['api_requests'],
            'success_rate': instance.metrics['successful_requests'] / max(1, instance.metrics['api_requests']),
            'avg_request_time': sum(request_times) / max(1, len(request_times)),
            'avg_image_time': sum(image_times) / max(1, len(image_times)),
            'uptime': instance.metrics['last_updated']
        }

app = FastAPI()
storage = KnowledgeStorage()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hello World"}

class QuestionRequest(BaseModel):
    question: Annotated[
        str, 
        StringConstraints(min_length=3, max_length=500)
    ] = Field(..., example="How to enable CORS?", description="Your question (3-500 chars)")
    
    image: Optional[str] = Field(
        None,
        example="iVBORw0KGgoAAAANSUhEUg...",
        description="Base64 encoded image (optional)",
        regex=r'^[A-Za-z0-9+/=]*$'
    )
    
    @field_validator('question')
    def sanitize_input(cls, v):
        if "<script>" in v.lower():
            raise ValueError("Invalid input")
        return v.strip()

@app.get("/metrics")
def get_metrics():
    return {
        "storage_metrics": storage.get_performance_stats(),
        "system_metrics": SystemMetrics.collect()
    }

@app.post(
    "/api/",
    summary="Get answers from Discourse/Docsify",
    response_description="List of relevant posts with scores",
    tags=["Q&A"],
    responses={
        400: {"description": "Invalid image format"},
        422: {"description": "Validation error"},
        500: {"description": "Internal server error"}
    }
)
async def answer_question(
    request: QuestionRequest,
    api_key: str = Header(None)
):
    start_time = time.perf_counter()
    cache_used = False
    try:
        query = request.question
        if request.image:
            query += "\nIMAGE CONTEXT:\n" + extract_text_from_image(request.image)
        
        discourse_data, from_cache1 = get_discourse_posts()
        docsify_data, from_cache2 = get_docsify_content()
        cache_used = from_cache1 or from_cache2

        results = []
        for post in discourse_data:
            score = max(
                fuzz.token_sort_ratio(query.lower(), post["title"].lower()),
                fuzz.token_sort_ratio(query.lower(), post["content"].lower())
            )
            if score > 65 or post["is_solution"]:
                results.append({
                    "source": "discourse",
                    "score": score,
                    "content": post["content"],
                    "url": post["url"],
                    "is_solution": post["is_solution"],
                    "date": post.get("date", datetime.now().isoformat())
                })
        
        for doc in docsify_data:
            score = fuzz.token_sort_ratio(query.lower(), doc["text"].lower())
            if score > 65:
                results.append({
                    "source": "docsify",
                    "score": score,
                    "content": doc["text"],
                    "url": doc["url"],
                    "date": doc.get("date", datetime.now().isoformat())
                })

        sorted_results = sorted(results, key=lambda x: (-x["score"], x["date"]))

        if not results or max(r["score"] for r in results) < ai_proxy.min_confidence:
            try:
                ai_response = await ai_proxy.get_fallback_answer(
                    question=request.question,
                    context="\n".join([r["content"] for r in results[:2]])
                )
                results.append(ai_response)
                sorted_results = sorted(results, key=lambda x: (-x["score"], x["date"]))
            except HTTPException as e:
                logger.warning(f"AI fallback failed: {e.detail}")
        
        return {
            "answer": "Combined results",
            "results": sorted_results,
            "metrics": {
                "processing_time_ms": (time.perf_counter() - start_time) * 1000,
                "sources_queried": ["discourse", "docsify"],
                "cache_used": cache_used
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))