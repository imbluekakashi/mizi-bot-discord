import os

from dotenv import load_dotenv
from groq import Groq


load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise RuntimeError("No se encontró GROQ_API_KEY en el archivo .env")


client = Groq(api_key=api_key)

models = client.models.list()

print("=== MODELOS DISPONIBLES ===")

for model in models.data:
    print(model.id)