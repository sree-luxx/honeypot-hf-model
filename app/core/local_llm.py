from huggingface_hub import AsyncInferenceClient
from app.config import HF_TOKEN, HF_MODEL_ID
import asyncio

class LocalLLM:
    def __init__(self):
        if not HF_TOKEN:
            print("Warning: HF_TOKEN not found in environment variables.")
        
        self.client = AsyncInferenceClient(token=HF_TOKEN)
        self.model = HF_MODEL_ID

    async def generate(self, prompt: str) -> str:
        try:
            messages = [{"role": "user", "content": prompt}]
            # Add a timeout to prevent hanging the request indefinitely
            # 25 seconds timeout to allow some buffer before 30s connection timeout
            response = await asyncio.wait_for(
                self.client.chat_completion(
                    messages=messages,
                    model=self.model,
                    max_tokens=100,
                    temperature=0.8
                ),
                timeout=25.0
            )
            return response.choices[0].message.content.strip()
        except asyncio.TimeoutError:
            print("Error: Hugging Face API timed out (25s limit).")
            return "Oh dear, I'm a bit confused right now. Can you explain that again slowly?"
        except Exception as e:
            print(f"Error generating response from Hugging Face: {e}")
            return "..."  # Fallback
