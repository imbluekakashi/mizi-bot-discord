from typing import List

from ai.provider import AIProvider
from ai.providers.groq_provider import GroqProvider
from ai.providers.openrouter_provider import OpenRouterProvider


PROVIDERS = {
    "groq": GroqProvider,
    "openrouter": OpenRouterProvider,
}


def create_provider(provider_name: str) -> AIProvider:
    provider_name = provider_name.lower().strip()

    provider_class = PROVIDERS.get(provider_name)

    if provider_class is None:
        raise ValueError(f"Proveedor de IA no soportado: {provider_name}")

    return provider_class()


class FallbackAIProvider(AIProvider):
    """
    Intenta generar con el primer proveedor de la lista. Si falla
    (rate limit, error de red, etc.), pasa al siguiente.
    """

    def __init__(self, provider_names: List[str]):
        self.providers = []

        for name in provider_names:
            try:
                self.providers.append((name, create_provider(name)))
            except Exception as error:
                print(f"No se pudo inicializar '{name}': {error}")

        if not self.providers:
            raise RuntimeError("No se pudo inicializar ningún proveedor de IA.")

    def generate(self, messages, model, temperature, max_tokens) -> str:
        last_error = None

        for name, provider in self.providers:
            try:
                return provider.generate(
                    messages=messages,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
            except Exception as error:
                print(f"Proveedor '{name}' falló: {error}")
                last_error = error

        raise last_error