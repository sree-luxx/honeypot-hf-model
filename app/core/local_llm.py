from huggingface_hub import InferenceClient
from app.config import HF_TOKEN, HF_MODEL_ID

class LocalLLM:
    def __init__(self):
        if not HF_TOKEN:
            print("Warning: HF_TOKEN not found in environment variables.")
        
        # Set a timeout (e.g., 20 seconds) to ensure we respond before the client (30s) times out
        self.client = InferenceClient(token=HF_TOKEN, timeout=20)
        self.model = HF_MODEL_ID

    def generate(self, prompt: str) -> str:
        try:
            # Using text-generation or chat-completion depending on the model
            # For Llama 3 instruct, chat completion is better if supported, 
            # but let's stick to text_generation for broad compatibility or structure the prompt manually.
            # Llama 3 uses specific tokens, but the InferenceClient might handle some.
            # Let's use simple text_generation with a good prompt structure.
            
            response = self.client.text_generation(
                prompt,
                model=self.model,
                max_new_tokens=100,
                temperature=0.8,
                return_full_text=False
            )
            return response.strip()
        except Exception as e:
            print(f"Error generating response from Hugging Face: {e}")
            # Fallback response to avoid empty replies on error/timeout
            return "I am confused, can you explain that again?"
