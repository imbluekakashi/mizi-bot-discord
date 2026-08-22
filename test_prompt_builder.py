from models.character import Character
from ai.prompt_builder import PromptBuilder


character = Character()

builder = PromptBuilder(character)

messages = builder.build_messages(
    "Hola Mizi, ¿quién eres y qué cosas te gustan?"
)

print("\n=== SYSTEM PROMPT ===\n")
print(messages[0]["content"])

print("\n=== USER MESSAGE ===\n")
print(messages[1]["content"])