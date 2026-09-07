from typing import List, Optional

from database.repositories.memory_repository import MemoryRepository


class LongTermMemory:
    """
    Recuerdos permanentes por usuario. A diferencia de
    ConversationMemory (historial reciente que se recorta solo),
    esto NO se recorta por antigüedad — solo se limita cuántos
    recuerdos se inyectan en el prompt en cada mensaje.
    """

    def __init__(
        self,
        repository: Optional[MemoryRepository] = None,
        max_facts_in_prompt: int = 15,
    ):
        self.repository = repository or MemoryRepository()
        self.max_facts_in_prompt = max_facts_in_prompt

    def add(self, user_id: str, content: str) -> None:
        content = content.strip()

        if not content:
            return

        # Evita duplicados exactos (el modelo a veces repite un
        # hecho que ya guardó en un mensaje anterior).
        existing = self.repository.get_memories(
            user_id=user_id,
            limit=self.max_facts_in_prompt,
        )

        if any(
            memory.content.strip().lower() == content.lower()
            for memory in existing
        ):
            return

        self.repository.add_memory(
            user_id=user_id,
            content=content,
        )

    def get_facts(self, user_id: str) -> List[str]:
        memories = self.repository.get_memories(
            user_id=user_id,
            limit=self.max_facts_in_prompt,
        )

        return [memory.content for memory in memories]
