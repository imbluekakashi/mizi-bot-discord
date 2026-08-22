from database.repositories.conversation_repository import (
    ConversationRepository,
)


repository = ConversationRepository()

conversation_id = "test_conversation_1"


print("=== CREANDO CONVERSACIÓN ===")

conversation = repository.create(
    conversation_id=conversation_id,
    character_id="mizi_test",
    user_id="test_user",
    guild_id="test_guild",
    channel_id="test_channel",
    title="Conversación de prueba",
)

print("Conversación creada.")
print("ID:", conversation.id)
print("Personaje:", conversation.character_id)
print("Usuario:", conversation.user_id)


print("\n=== GUARDANDO MENSAJES ===")

repository.add_message(
    conversation_id=conversation_id,
    role="user",
    content="Hola Mizi, ¿cómo estás?",
)

repository.add_message(
    conversation_id=conversation_id,
    role="assistant",
    content="¡Holi! Estoy bien :3 ¿Y tú?",
)

print("Mensajes guardados.")


print("\n=== RECUPERANDO MENSAJES ===")

messages = repository.get_messages(
    conversation_id
)

for message in messages:
    print(f"[{message.role}] {message.content}")