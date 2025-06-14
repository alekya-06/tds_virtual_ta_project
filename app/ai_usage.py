import openai
from fastapi import HTTPException
from app.config import settings

token = settings.AIPIPE_TOKEN


class AIProxy:
    def __init__(self):
        self.client = openai.OpenAI(
            base_url=settings.AIPIPE_BASE_URL,
            api_key=settings.AIPIPE_TOKEN
        )
        self.min_confidence = 0.65  # Use AI if local score < 65%

    async def get_fallback_answer(self, question: str, context: str = "") -> dict:
        """Fallback to AI Pipe when local results are poor"""
        try:
            response = self.client.chat.completions.create(
                model=ALLOWED_MODELS["default"],
                messages=[
                    {
                        "role": "system",
                        "content": f"Use this context if relevant:\n{context}"
                    },
                    {"role": "user", "content": question}
                ],
                temperature=0.3,
                max_tokens=500
            )
            return {
                "source": "aipipe",
                "model": ALLOWED_MODELS["default"],
                "content": response.choices[0].message.content,
                "cost": response.usage.total_tokens / 1000 * 0.002  # Estimate cost
            }
        except Exception as e:
            # Fallback to cheaper model if budget exhausted
            try:
                response = self.client.chat.completions.create(
                    model=ALLOWED_MODELS["fallback"],
                    messages=[{"role": "user", "content": question}],
                    temperature=0.3
                )
                return {
                    "source": "aipipe-fallback",
                    "model": ALLOWED_MODELS["fallback"],
                    "content": response.choices[0].message.content
                }
            except Exception as e:
                raise HTTPException(
                    status_code=429,
                    detail="AI quota exceeded. Try again later."
                )

ai_proxy = AIProxy()