from characters.manager import CharacterManager
from models.character import Character


manager = CharacterManager()

character_id = "mizi_test"


print("=== COMPROBANDO PERSONAJE ===")

loaded = manager.get(character_id)

if loaded:
    print("El personaje ya existe en la base de datos.")
    print("Nombre:", loaded.identity.name)
    print("Nombre visible:", loaded.identity.display_name)

else:
    print("El personaje no existe. Creándolo...")

    mizi = Character()

    manager.create(
        character_id=character_id,
        character=mizi,
    )

    print("Personaje creado correctamente.")


print("\n=== COMPROBANDO PERSISTENCIA ===")

loaded = manager.get(character_id)

if loaded:
    print("Personaje encontrado en SQLite.")
    print("Nombre:", loaded.identity.name)
    print("Proveedor:", loaded.ai_settings.provider)
    print("Modelo:", loaded.ai_settings.model)
else:
    print("ERROR: no se encontró el personaje.")