from typing import Dict, Optional

from database.repositories.character_repository import CharacterRepository
from models.character import Character


class CharacterManager:
    def __init__(self):
        self.repository = CharacterRepository()

    def create(
        self,
        character_id: str,
        character: Character,
    ) -> Character:

        self.repository.create(
            character_id=character_id,
            data=character.to_dict(),
        )

        return character

    def get(
        self,
        character_id: str,
    ) -> Optional[Character]:

        saved_character = self.repository.get(character_id)

        if saved_character is None:
            return None

        return Character.from_dict(saved_character.data)

    def update(
        self,
        character_id: str,
        character: Character,
    ) -> Optional[Character]:

        saved_character = self.repository.update(
            character_id=character_id,
            data=character.to_dict(),
        )

        if saved_character is None:
            return None

        return Character.from_dict(saved_character.data)

    def delete(
        self,
        character_id: str,
    ) -> bool:

        return self.repository.delete(character_id)

    def exists(
        self,
        character_id: str,
    ) -> bool:

        return self.repository.get(character_id) is not None