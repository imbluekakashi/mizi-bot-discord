from typing import Optional

from sqlalchemy import select

from database.database import SessionLocal
from database.models import CharacterModel


class CharacterRepository:

    def create(
        self,
        character_id: str,
        data: dict,
    ) -> CharacterModel:

        with SessionLocal() as session:

            character = CharacterModel(
                id=character_id,
                data=data,
            )

            session.add(character)
            session.commit()
            session.refresh(character)

            return character

    def get(
        self,
        character_id: str,
    ) -> Optional[CharacterModel]:

        with SessionLocal() as session:

            statement = select(CharacterModel).where(
                CharacterModel.id == character_id
            )

            return session.scalar(statement)

    def update(
        self,
        character_id: str,
        data: dict,
    ) -> Optional[CharacterModel]:

        with SessionLocal() as session:

            statement = select(CharacterModel).where(
                CharacterModel.id == character_id
            )

            character = session.scalar(statement)

            if character is None:
                return None

            character.data = data

            session.commit()
            session.refresh(character)

            return character

    def delete(
        self,
        character_id: str,
    ) -> bool:

        with SessionLocal() as session:

            statement = select(CharacterModel).where(
                CharacterModel.id == character_id
            )

            character = session.scalar(statement)

            if character is None:
                return False

            session.delete(character)
            session.commit()

            return True