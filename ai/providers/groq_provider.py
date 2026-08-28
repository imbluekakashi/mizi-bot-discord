import os

from groq import Groq

from ai.provider import AIProvider


class GroqProvider(AIProvider):
    """Proveedor de IA utilizando Groq."""

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise RuntimeError(
                "No se encontró GROQ_API_KEY en el archivo .env"
            )

self.client = Groq(api_key=api_key, timeout=30.0)

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
            raise RuntimeError(
                "El modelo no devolvió contenido."
            )

        return content
