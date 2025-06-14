# API Configuration
AIPIPE_TOKEN = "your_aipipe_token"  # From your email
AIPIPE_BASE_URL = "https://aipipe.org/openai/v1"  # or /openrouter/v1
ALLOWED_MODELS = {
    "default": "openai/gpt-4.1-nano",
    "fallback": "openai/gpt-3.5-turbo"
}