from datetime import datetime
import time
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Tuple
from .storage import KnowledgeStorage
from .config import DATE_RANGES, DISCOURSE_URL, DOCSIFY_BASE

storage = KnowledgeStorage()

def rate_limited_get(url: str, retries: int = 3) -> requests.Response:
    """Make HTTP requests with rate limiting and retries"""
    for attempt in range(retries):
        try:
            time.sleep(0.5)  # Rate limiting
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response
        except (requests.RequestException, requests.Timeout) as e:
            if attempt == retries - 1:
                raise
            time.sleep(1 * (attempt + 1))

def get_discourse_posts() -> Tuple[List[Dict], bool]:
    """Fetch Discourse posts with caching"""
    # First check in-memory cache
    cached_data = storage.get_cached_data("discourse")
    if cached_data:
        return cached_data, True
    
    # Then check database cache
    db_posts, from_db_cache = storage.get_recent_posts("discourse")
    if from_db_cache:
        storage.set_cached_data("discourse", db_posts)
        return db_posts, True

    # Fresh scrape if no cache
    posts = []
    page = 0
    while True:
        try:
            response = rate_limited_get(f"{DISCOURSE_URL}?page={page}&order=created")
            data = response.json()
            topics = data.get("topic_list", {}).get("topics", [])
            if not topics:
                break
                
            for topic in topics:
                created_at = datetime.strptime(topic["created_at"][:10], "%Y-%m-%d").date()
                if DATE_RANGES["discourse"][0] <= created_at <= DATE_RANGES["discourse"][1]:
                    posts.append({
                        "source": "discourse",
                        "title": topic["title"],
                        "content": BeautifulSoup(topic["excerpt"], "html.parser").get_text(),
                        "url": f"{DISCOURSE_URL}/t/{topic['slug']}/{topic['id']}",
                        "date": topic["created_at"],
                        "is_solution": topic.get("has_accepted_answer", False)
                    })
            page += 1
        except Exception as e:
            break
    
    if posts:
        storage.save_posts(posts)
        storage.set_cached_data("discourse", posts)
    return posts, False

def get_docsify_content() -> Tuple[List[Dict], bool]:
    """Fetch Docsify content with caching"""
    # First check in-memory cache
    cached_data = storage.get_cached_data("docsify")
    if cached_data:
        return cached_data, True
    
    # Then check database cache
    db_content, from_db_cache = storage.get_recent_posts("docsify")
    if from_db_cache:
        storage.set_cached_data("docsify", db_content)
        return db_content, True

    # Fresh scrape if no cache
    content = []
    known_files = [
        "README.md",
        "_sidebar.md",
        "development-tools.md",
        "vscode.md",
        "github-copilot.md",
        "uv.md",
        "npx.md",
        "unicode.md",
        "devtools.md",
        "css-selectors.md",
        "json.md",
        "bash.md",
        "llm.md",
        "spreadsheets.md",
        "sqlite.md",
        "git.md",
        "deployment-tools.md",
        "markdown.md",
        "image-compression.md",
        "github-pages.md",
        "colab.md",
        "vercel.md",
        "github-actions.md",
        "docker.md",
        "github-codespaces.md",
        "ngrok.md",
        "cors.md",
        "rest-apis.md",
        "fastapi.md",
        "google-auth.md",
        "ollama.md",
        "prompt-engineering.md",
        "tds-ta-instructions.md",
        "tds-gpt-reviewer.md",
        "llm-sentiment-analysis.md",
        "llm-text-extraction.md",
        "base64-encoding.md",
        "vision-models.md",
        "embeddings.md",
        "multimodal-embeddings.md",
        "topic-modeling.md",
        "vector-databases.md",
        "rag-cli.md",
        "hybrid-rag-typesense.md",
        "function-calling.md",
        "llm-agents.md",
        "llm-image-generation.md",
        "llm-speech.md",
        "llm-evals.md",
        "project-tds-virtual-ta.md",
        "data-sourcing.md",
        "scraping-with-excel.md",
        "scraping-with-google-sheets.md",
        "crawling-cli.md",
        "bbc-weather-api-with-python.md",
        "scraping-imdb-with-javascript.md",
        "nominatim-api-with-python.md",
        "wikipedia-data-with-python.md",
        "scraping-pdfs-with-tabula.md",
        "convert-pdfs-to-markdown.md",
        "convert-html-to-markdown.md",
        "llm-website-scraping.md",
        "llm-video-screen-scraping.md",
        "web-automation-with-playwright.md",
        "scheduled-scraping-with-github-actions.md",
        "scraping-emarketer.md",
        "scraping-live-sessions.md",
        "data-preparation.md",
        "data-cleansing-in-excel.md",
        "data-transformation-in-excel.md",
        "splitting-text-in-excel.md",
        "data-aggregation-in-excel.md",
        "data-preparation-in-the-shell.md",
        "data-preparation-in-the-editor.md",
        "data-preparation-in-duckdb.md",
        "parsing-json.md",
        "cleaning-data-with-openrefine.md",
        "dbt.md",
        "transforming-images.md",
        "extracting-audio-and-transcripts.md",
        "correlation-with-excel.md",
        "regression-with-excel.md",
        "forecasting-with-excel.md",
        "outlier-detection-with-excel.md",
        "data-analysis-with-python.md",
        "data-analysis-with-sql.md",
        "data-analysis-with-datasette.md",
        "data-analysis-with-duckdb.md",
        "data-analysis-with-chatgpt.md",
        "geospatial-analysis-with-excel.md",
        "geospatial-analysis-with-python.md",
        "geospatial-analysis-with-qgis.md",
        "network-analysis-in-python.md",
        "data-visualization.md",
        "visualizing-forecasts-with-excel.md",
        "visualizing-animated-data-with-powerpoint.md",
        "visualizing-animated-data-with-flourish.md",
        "visualizing-network-data-with-kumu.md",
        "visualizing-charts-with-excel.md",
        "data-visualization-with-seaborn.md",
        "data-visualization-with-chatgpt.md",
        "actor-network-visualization.md",
        "rawgraphs.md",
        "data-storytelling.md",
        "narratives-with-llms.md",
        "marimo.md",
        "revealjs.md",
        "marp.md"
    ]
    
    for file in known_files:
        try:
            response = rate_limited_get(f"{DOCSIFY_BASE}{file}")
            if response.status_code == 200:
                last_modified = response.headers.get("Last-Modified", "")
                if DATE_RANGES["docsify"][0] <= last_modified[:10] <= DATE_RANGES["docsify"][1]:
                    content.append({
                        "source": "docsify",
                        "text": response.text,
                        "url": f"{DOCSIFY_BASE}{file}",
                        "date": last_modified
                    })
        except Exception:
            continue
    
    if content:
        storage.save_posts(content)
        storage.set_cached_data("docsify", content)
    return content, False