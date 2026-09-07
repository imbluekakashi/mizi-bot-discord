import time
from typing import List, Optional

from sqlalchemy import select

from database.database import SessionLocal
from database.models import MemoryModel


class MemoryRepository:

    def add_memory(
        self,
        user_id: str,
        content: str,
    ) -> MemoryModel:

        with SessionLocal() as session:

            memory = MemoryModel(
                user_id=user_id,
                content=content,
                created_at=time.time(),
            )

            session.add(memory)
            session.commit()
            session.refresh(memory)

            return memory

    def get_memories(
        self,
        user_id: str,
        limit: int = 20,
    ) -> List[MemoryModel]:

        with SessionLocal() as session:

            statement = (
                select(MemoryModel)
                .where(MemoryModel.user_id == user_id)
                .order_by(MemoryModel.id.desc())
                .limit(limit)
            )

            memories = list(
                session.scalars(statement).all()
            )

            memories.reverse()

            return memories

    def count_memories(
        self,
        user_id: str,
    ) -> int:

        with SessionLocal() as session:

            statement = select(MemoryModel).where(
                MemoryModel.user_id == user_id
            )

            return len(
                list(session.scalars(statement).all())
            )

    def delete_memory(
        self,
        memory_id: int,
    ) -> bool:

        with SessionLocal() as session:

            statement = select(MemoryModel).where(
                MemoryModel.id == memory_id
            )

            memory = session.scalar(statement)

            if memory is None:
                return False

            session.delete(memory)
            session.commit()

            return True

    def delete_all_for_user(
        self,
        user_id: str,
    ) -> int:

        with SessionLocal() as session:

            statement = select(MemoryModel).where(
                MemoryModel.user_id == user_id
            )

            memories = list(
                session.scalars(statement).all()
            )

            count = len(memories)

            for memory in memories:
                session.delete(memory)

            session.commit()

            return count
