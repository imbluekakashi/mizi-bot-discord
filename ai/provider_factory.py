import time
from typing import Iterable

from ai.provider import AIProvider
from ai.provider_monitor import ProviderMonitor

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
    "gemini": "gemini-3.5-flash-lite",
    "sambanova": "Meta-Llama-3.3-70B-Instruct",
    "openrouter": "openrouter/free",
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

        names = [
            name.lower().strip()
            for name in provider_names
        ]

        self.monitor = ProviderMonitor(names)

        for name in names:
            try:
                provider = create_provider(name)
                self.providers.append((name, provider))

                print(
                    f"[AI] Proveedor disponible: {name} "
                    f"(modelo: {self.get_model(name)})"
                )

            except Exception as error:
                print(
                    f"[AI] No se pudo inicializar "
                    f"'{name}': {error}"
                )

        if not self.providers:
            raise RuntimeError(
                "No se pudo inicializar ningún proveedor de IA."
            )

    def get_model(self, provider_name: str) -> str:
        return self.provider_models.get(
            provider_name,
            DEFAULT_MODELS.get(provider_name, ""),
        )

    @staticmethod
    def _is_rate_limit(error: Exception) -> bool:
        text = str(error).lower()

        markers = (
            "429",
            "rate limit",
            "rate_limit",
            "too many requests",
            "quota",
            "resource_exhausted",
            "resource exhausted",
        )

        return any(marker in text for marker in markers)

    def generate(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float = 0.85,
        max_tokens: int = 450,
    ) -> str:

        last_error: Exception | None = None

        input_text = "\n".join(
            message.get("content", "")
            for message in messages
        )

        for name, provider in self.providers:
            state = next(
                (
                    item
                    for item in self.monitor.snapshot()
                    if item.provider == name
                ),
                None,
            )

            # No desperdiciar peticiones en un proveedor que acaba
            # de devolver un 429. Después del cooldown se prueba otra vez.
            if (
                state
                and state.status == "limited"
                and time.time() < state.limited_until_ts
            ):
                print(
                    f"[AI] Saltando {name}: temporalmente limitado."
                )
                continue

            selected_model = self.get_model(name)

            if (
                model
                and name not in self.provider_models
            ):
                selected_model = model

            started = time.monotonic()

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

                latency_ms = (
                    time.monotonic() - started
                ) * 1000

                self.monitor.record(
                    name,
                    success=True,
                    rate_limited=False,
                    input_text=input_text,
                    output_text=result,
                    latency_ms=latency_ms,
                )

                print(
                    f"[AI] Respuesta obtenida desde {name} "
                    f"({latency_ms:.0f} ms)."
                )

                return result

            except Exception as error:
                latency_ms = (
                    time.monotonic() - started
                ) * 1000

                rate_limited = self._is_rate_limit(error)

                self.monitor.record(
                    name,
                    success=False,
                    rate_limited=rate_limited,
                    input_text=input_text,
                    output_text="",
                    latency_ms=latency_ms,
                    error_text=str(error),
                )

                print(
                    f"[AI] {name} falló "
                    f"({latency_ms:.0f} ms): {error}"
                )

                last_error = error

        if last_error is not None:
            raise last_error

        raise RuntimeError(
            "Todos los proveedores de IA están temporalmente "
            "limitados o fallaron."
        )
