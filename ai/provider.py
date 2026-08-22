from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Interfaz común para todos los proveedores de IA."""

    @abstractmethod
    def generate(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Genera una respuesta usando el proveedor."""
        raise NotImplementedError