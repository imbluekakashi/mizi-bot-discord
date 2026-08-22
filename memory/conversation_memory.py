from typing import Dict, List, Optional

from database.repositories.conversation_repository import ConversationRepository


class ConversationMemory:
    """
    Traduce el historial guardado en la base de datos al formato
    de mensajes que usa PromptBuilder / los proveedores de IA.
    """

    def __init__(
        self,
        repository: Optional[ConversationRepository] = None,
        history_limit: int = 20,
    ):
        self.repository = repository or ConversationRepository()
        self.history_limit = history_limit

    @staticmethod
    def build_conversation_id(channel_id: str, user_id: str) -> str:
        # Cada usuario tiene su propia conversación con Mizi dentro
        # de un mismo canal, para que no se mezclen identidades.
        return f"{channel_id}:{user_id}"

    def ensure_conversation(
        self,
        conversation_id: str,
        character_id: str,
        user_id: str,
        guild_id: Optional[str],
        channel_id: Optional[str],
    ):
        return self.repository.get_or_create(
            conversation_id=conversation_id,
            character_id=character_id,
            user_id=user_id,
            guild_id=guild_id,
            channel_id=channel_id,
        )

    def get_history(self, conversation_id: str) -> List[Dict[str, str]]:
        messages = self.repository.get_recent_messages(
            conversation_id=conversation_id,
            limit=self.history_limit,
        )

        return [
            {"role": message.role, "content": message.content}
            for message in messages
        ]

    def add_user_message(self, conversation_id: str, content: str):
        self.repository.add_message(
            conversation_id=conversation_id,
            role="user",
            content=content,
        )

    def add_assistant_message(self, conversation_id: str, content: str):
        self.repository.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=content,
        )