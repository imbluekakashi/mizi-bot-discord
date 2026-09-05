import os

from google import genai
from google.genai import types

from ai.provider import AIProvider


class GeminiProvider(AIProvider):
    DEFAULT_MODEL = "gemini-2.5-flash-lite"

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "No se encontró GEMINI_API_KEY en las variables de entorno."
            )

        self.client = genai.Client(api_key=api_key)

    @staticmethod
    def _convert_messages(messages: list[dict[str, str]]) -> tuple[str, list]:
        system_parts = []
        history = []

        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")

            if not content:
                continue

            if role == "system":
                system_parts.append(content)
                continue

            gemini_role = "model" if role == "assistant" else "user"

            history.append(
                types.Content(
                    role=gemini_role,
                    parts=[types.Part(text=content)],
                )
            )

        system_instruction = "\n\n".join(system_parts)

        return system_instruction, history

    def generate(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.85,
        max_tokens: int = 450,
    ) -> str:

        model = model or self.DEFAULT_MODEL

        system_instruction, history = self._convert_messages(messages)

        if not history:
            raise RuntimeError("Gemini recibió una conversación vacía.")

        last_message = history.pop()

        if last_message.role != "user":
            history.append(last_message)
            prompt = ""
        else:
            prompt = last_message.parts[0].text

        config = types.GenerateContentConfig(
            system_instruction=system_instruction or None,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        response = self.client.models.generate_content(
            model=model,
            contents=history + [
                types.Content(
                    role="user",
                    parts=[types.Part(text=prompt)],
                )
            ],
            config=config,
        )

        content = response.text

        if not content:
            raise RuntimeError("Gemini no devolvió contenido.")

        return content.strip()
