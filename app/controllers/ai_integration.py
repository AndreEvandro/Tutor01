import os
from openai import OpenAI
from app.config import settings

class AIIntegrationController:
    def __init__(self):
        api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")
        self.client = OpenAI(api_key=api_key) if api_key else None

    def generate_response(self, system_prompt: str, user_prompt: str) -> str | None:
        """
        Envia a solicitação para a API da OpenAI se houver chave configurada.
        Retorna None se a chave não estiver configurada ou se houver erro.
        """
        if not self.client or not settings.OPENAI_API_KEY:
            return None

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Erro ao conectar com a API OpenAI: {e}")
            return None