from typing import List, Optional

from sqlalchemy import select

from database.database import SessionLocal
from database.models import ConversationModel, MessageModel


class ConversationRepository:

    def create(
        self,
        conversation_id: str,
        character_id: str,
        user_id: str,
        guild_id: Optional[str] = None,
        channel_id: Optional[str] = None,
        title: str = "Nueva conversación",
    ) -> ConversationModel:

        with SessionLocal() as session:

            conversation = ConversationModel(
                id=conversation_id,
                character_id=character_id,
                user_id=user_id,
                guild_id=guild_id,
                channel_id=channel_id,
                title=title,
            )

            session.add(conversation)
            session.commit()
            session.refresh(conversation)

            return conversation

    def get(
        self,
        conversation_id: str,
    ) -> Optional[ConversationModel]:

        with SessionLocal() as session:

            statement = select(ConversationModel).where(
                ConversationModel.id == conversation_id
            )

            return session.scalar(statement)

    def get_or_create(
        self,
        conversation_id: str,
        character_id: str,
        user_id: str,
        guild_id: Optional[str] = None,
        channel_id: Optional[str] = None,
        title: str = "Nueva conversación",
    ) -> ConversationModel:

        conversation = self.get(conversation_id)

        if conversation is not None:
            return conversation

        return self.create(
            conversation_id=conversation_id,
            character_id=character_id,
            user_id=user_id,
            guild_id=guild_id,
            channel_id=channel_id,
            title=title,
        )

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
    ) -> MessageModel:

        with SessionLocal() as session:

            message = MessageModel(
                conversation_id=conversation_id,
                role=role,
                content=content,
            )

            session.add(message)
            session.commit()
            session.refresh(message)

            return message

    def get_messages(
        self,
        conversation_id: str,
    ) -> List[MessageModel]:

        with SessionLocal() as session:

            statement = (
                select(MessageModel)
                .where(
                    MessageModel.conversation_id == conversation_id
                )
                .order_by(MessageModel.id)
            )

            return list(session.scalars(statement).all())

    def get_recent_messages(
        self,
        conversation_id: str,
        limit: int = 20,
    ) -> List[MessageModel]:

        with SessionLocal() as session:

            statement = (
                select(MessageModel)
                .where(
                    MessageModel.conversation_id == conversation_id
                )
                .order_by(MessageModel.id.desc())
                .limit(limit)
            )

            messages = list(
                session.scalars(statement).all()
            )

            messages.reverse()

            return messages