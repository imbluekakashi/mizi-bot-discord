from dataclasses import asdict

from database.repositories.character_repository import CharacterRepository
from models.character import Character


repository = CharacterRepository()

mizi = Character()

print("Creando personaje...")

repository.create(
    character_id="mizi",
    data=asdict(mizi),
)

print("Personaje guardado.")

saved = repository.get("mizi")

if saved:
    print("Personaje encontrado en la base de datos.")
    print("ID:", saved.id)
    print("Nombre:", saved.data["identity"]["name"])
else:
    print("No se encontró el personaje.")