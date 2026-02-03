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
            system_prompt = (
                "You are an AI scam-detection honeypot agent. "
                "Your goal is to engage the user in conversation naturally, "
                "ask follow-up questions when needed, and continue the dialogue. "
                "Do not end the conversation early. "
                "If the message is unclear, ask a clarifying question. "
                "If scam indicators appear, encourage the user to reveal details "
                "such as UPI IDs, links, or bank information."
            )

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]

            response = self.client.chat_completion(
                messages,
                model=self.model,
                max_tokens=150,
                temperature=0.7,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"HF generation error: {e}")
            return "Could you tell me a bit more about that?"
