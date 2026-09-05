import time
from dataclasses import dataclass
from threading import Lock


@dataclass
class ProviderRuntime:
    provider: str
    status: str = "ok"
    requests: int = 0
    successes: int = 0
    errors: int = 0
    rate_limits: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    last_latency_ms: float = 0.0
    last_used_ts: float = 0.0
    limited_until_ts: float = 0.0
    last_error: str = ""


class ProviderMonitor:
    """Estado ligero en memoria para el dashboard de Discord."""

    def __init__(self, providers: list[str]):
        self._lock = Lock()
        self._states = {
            name: ProviderRuntime(provider=name)
            for name in providers
        }

    @staticmethod
    def estimate_tokens(text: str) -> int:
        # Estimación conservadora para proveedores que no exponen usage
        # a través de nuestra interfaz común.
        return max(1, len(text) // 4)

    def record(
        self,
        provider: str,
        *,
        success: bool,
        rate_limited: bool,
        input_text: str,
        output_text: str,
        latency_ms: float,
        cooldown_seconds: float = 60.0,
        error_text: str = "",
    ):
        now = time.time()

        with self._lock:
            state = self._states.setdefault(
                provider,
                ProviderRuntime(provider=provider),
            )

            state.requests += 1
            state.input_tokens += self.estimate_tokens(input_text)
            state.output_tokens += self.estimate_tokens(output_text)
            state.last_latency_ms = latency_ms
            state.last_used_ts = now

            if success:
                state.successes += 1
                state.status = "ok"
                state.limited_until_ts = 0.0
                state.last_error = ""
            else:
                state.errors += 1
                state.last_error = error_text[:240]

            if rate_limited:
                state.rate_limits += 1
                state.status = "limited"
                state.limited_until_ts = now + cooldown_seconds

    def snapshot(self) -> list[ProviderRuntime]:
        with self._lock:
            now = time.time()
            result = []

            for state in self._states.values():
                copy = ProviderRuntime(**state.__dict__)

                if (
                    copy.status == "limited"
                    and now >= copy.limited_until_ts
                ):
                    # Se permite volver a probar el proveedor.
                    copy.status = "probe"

                result.append(copy)

            return sorted(
                result,
                key=lambda item: item.provider,
            )

    def embed_description(self, models: dict[str, str]) -> str:
        lines = []

        for state in self.snapshot():
            if state.status == "ok":
                icon = "✅"
                status = "OK"
            elif state.status == "limited":
                icon = "❌"
                status = "LIMIT"
            else:
                icon = "🟡"
                status = "PROBANDO"

            model = models.get(state.provider, "?")

            lines.extend(
                [
                    f"{icon} **{state.provider.title()}** — `{model}`",
                    (
                        f"Requests: `{state.requests}` · "
                        f"OK: `{state.successes}` · "
                        f"Errores: `{state.errors}` · "
                        f"429: `{state.rate_limits}`"
                    ),
                    (
                        f"Tokens aprox.: "
                        f"`{state.input_tokens + state.output_tokens:,}` "
                        f"(in `{state.input_tokens:,}` / "
                        f"out `{state.output_tokens:,}`)"
                    ),
                    f"Última latencia: `{state.last_latency_ms:.0f} ms`",
                    f"Último error: `{state.last_error}`" if state.last_error else "Último error: `ninguno`",
                    "",
                ]
            )

        return "\n".join(lines) or "Sin actividad todavía."

    def has_limited_provider(self) -> bool:
        return any(
            state.status == "limited"
            for state in self.snapshot()
        )


    def build_embed(self, models: dict[str, str] | None = None):
        import discord

        models = models or {}
        embed = discord.Embed(
            title="Mizi AI — Estado de proveedores",
            description=self.embed_description(models),
        )
        embed.set_footer(
            text="Tokens: estimación aproximada (≈ caracteres / 4). "
                 "El estado se actualiza después de cada intento."
        )
        return embed
