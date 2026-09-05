from typing import Iterable

from ai.provider import AIProvider

from ai.providers.cerebras_provider import CerebrasProvider
from ai.providers.gemini_provider import GeminiProvider
from ai.providers.groq_provider import GroqProvider
from ai.providers.openrouter_provider import OpenRouterProvider
from ai.providers.sambanova_provider import SambaNovaProvider


PROVIDERS: dict[str, type[AIProvider]] = {
    "cerebras": CerebrasProvider,
    "groq": GroqProvider,
    "gemini": GeminiProvider,
    "sambanova": SambaNovaProvider,
    "openrouter": OpenRouterProvider,
}


DEFAULT_MODELS = {
    "cerebras": "gpt-oss-120b",
    "groq": "openai/gpt-oss-20b",
    "gemini": "gemini-2.5-flash-lite",
    "sambanova": "Meta-Llama-3.3-70B-Instruct",
    "openrouter": "openai/gpt-oss-20b:free",
}


def create_provider(provider_name: str) -> AIProvider:
    provider_name = provider_name.lower().strip()

    provider_class = PROVIDERS.get(provider_name)

    if provider_class is None:
        raise ValueError(
            f"Proveedor de IA no soportado: {provider_name}"
        )

    return provider_class()


class FallbackAIProvider(AIProvider):

    def __init__(
        self,
        provider_names: Iterable[str],
        provider_models: dict[str, str] | None = None,
    ):
        self.provider_models = provider_models or DEFAULT_MODELS.copy()

        self.providers: list[tuple[str, AIProvider]] = []

        for name in provider_names:
            name = name.lower().strip()

            try:
                provider = create_provider(name)

                self.providers.append(
                    (name, provider)
                )

                print(
                    f"[AI] Proveedor disponible: {name} "
                    f"(modelo: {self.get_model(name)})"
                )

            except Exception as error:
                print(
                    f"[AI] No se pudo inicializar '{name}': {error}"
                )

        if not self.providers:
            raise RuntimeError(
                "No se pudo inicializar ningún proveedor de IA."
            )

    def get_model(self, provider_name: str) -> str:
        return self.provider_models.get(
            provider_name,
            DEFAULT_MODELS.get(
                provider_name,
                "",
            ),
        )

    def generate(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.85,
        max_tokens: int = 450,
    ) -> str:

        last_error: Exception | None = None

        for name, provider in self.providers:

            selected_model = self.get_model(name)

            # Si el modelo fue especificado manualmente
            # y no hay uno específico para el proveedor,
            # se usa el modelo recibido.
            if (
                model
                and name not in self.provider_models
            ):
                selected_model = model

            try:
                print(
                    f"[AI] Intentando {name} "
                    f"con {selected_model}..."
                )

                result = provider.generate(
                    messages=messages,
                    model=selected_model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                print(
                    f"[AI] Respuesta obtenida desde {name}."
                )

                return result

            except Exception as error:
                print(
                    f"[AI] {name} falló: {error}"
                )

                last_error = error

        if last_error is not None:
            raise last_error

        raise RuntimeError(
            "Todos los proveedores de IA fallaron."
        )
