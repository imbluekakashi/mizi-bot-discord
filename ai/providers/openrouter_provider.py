import os

from openai import OpenAI

from ai.provider import AIProvider


class OpenRouterProvider(AIProvider):
    """Proveedor de IA utilizando OpenRouter (API compatible con OpenAI)."""

    def __init__(self):
        api_key = os.getenv("OPENROUTER_API_KEY")

        if not api_key:
            raise RuntimeError(
                "No se encontró OPENROUTER_API_KEY en el archivo .env"
            )

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )

    def generate(
        self,
        messages: list[dict[str, str]],
        model: str = "openai/gpt-oss-20b",
        temperature: float = 0.85,
        max_tokens: int = 150,
    ) -> str:

        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        content = response.choices[0].message.content

        if not content:
            raise RuntimeError("El modelo no devolvió contenido.")

        return content