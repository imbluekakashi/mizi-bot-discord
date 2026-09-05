import os

from openai import OpenAI

from ai.provider import AIProvider


class CerebrasProvider(AIProvider):
    DEFAULT_MODEL = "gpt-oss-120b"

    def __init__(self):
        api_key = os.getenv("CEREBRAS_API_KEY")

        if not api_key:
            raise RuntimeError(
                "No se encontró CEREBRAS_API_KEY en las variables de entorno."
            )

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.cerebras.ai/v1",
            timeout=30.0,
        )

    def generate(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.85,
        max_tokens: int = 450,
    ) -> str:

        model = model or self.DEFAULT_MODEL

        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        content = response.choices[0].message.content

        if not content:
            raise RuntimeError("Cerebras no devolvió contenido.")

        return content.strip()
