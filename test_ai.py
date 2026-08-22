import os

from dotenv import load_dotenv
from groq import Groq


load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

response = client.chat.completions.create(
    model="openai/gpt-oss-20b",
    messages=[
        {
            "role": "system",
            "content": (
                "Eres Mizi Miyaku, una elfa amable, curiosa "
                "y carismática. Responde de forma natural y breve."
            ),
        },
        {
            "role": "user",
            "content": "Hola Mizi, ¿cómo estás?",
        },
    ],
    temperature=0.85,
    max_tokens=100,
)

print("=== RESPUESTA COMPLETA ===")
print(response)

print("\n=== CHOICES ===")
print(response.choices)

if response.choices:
    print("\n=== MESSAGE ===")
    print(response.choices[0].message)

    print("\n=== CONTENT ===")
    print(repr(response.choices[0].message.content))