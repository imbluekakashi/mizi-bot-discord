from models.character import Character


mizi = Character()


print("=== PERSONAJE ===")
print(f"Nombre: {mizi.identity.name}")
print(f"Nombre visible: {mizi.identity.display_name}")

print("\n=== PERSONALIDAD ===")
print("Rasgos:", ", ".join(mizi.personality.traits))
print("Temperamento:", mizi.personality.temperament)

print("\n=== FORMA DE HABLAR ===")
print("Vocabulario:", mizi.speech.vocabulary)

print("\n=== LORE ===")
print("Mundo:", mizi.lore.world)
print("Relaciones:", mizi.lore.relationships)

print("\n=== IA ===")
print("Proveedor:", mizi.ai_settings.provider)
print("Modelo:", mizi.ai_settings.model)