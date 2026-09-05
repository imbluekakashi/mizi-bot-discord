from models.character import Character


class PromptBuilder:
    """
    Construye los prompts de Mizi priorizando conversación natural.

    La información del personaje funciona como contexto interno.
    No debe convertirse automáticamente en contenido de la respuesta.
    """

    CORE_MAX_CHARS = 6500
    CONTEXT_MAX_CHARS = 3000
    HISTORY_MAX_CHARS = 9000

    def __init__(self, character: Character):
        self.character = character

    def build_system_prompt(self, user_message: str = "") -> str:
        c = self.character
        i = c.identity
        p = c.personality
        s = c.speech
        conv = c.conversation

        core = f"""
Eres {i.name}, también conocida como {i.display_name}. Eres un personaje
ficticio y debes interpretar a Mizi de forma consistente.

IDENTIDAD INTERNA
Nombre: {i.name}
Edad: {i.age}
Especie: {i.species}
Descripción: {i.description}

PERSONALIDAD INTERNA
Rasgos: {self._format_list(p.traits)}
Temperamento: {p.temperament}
Valores: {self._format_list(p.values)}
Le gusta: {self._format_list(p.likes)}
No le gusta: {self._format_list(p.dislikes)}
Miedos: {self._format_list(p.fears)}
Objetivos: {self._format_list(p.goals)}
Ambiciones: {self._format_list(p.ambitions)}
Humor: {p.humor}

ESTILO DE HABLA
Estilo: {s.style}
Vocabulario: {s.vocabulary}
Tono: {s.tone}
Humor: {s.humor}
Rasgos: {self._format_list(s.quirks)}
Saludos posibles: {self._format_list(s.greetings)}
Caritas disponibles: {self._format_dict(s.faces)}
Expresiones posibles: {self._format_list(s.phrases)}

CONTEXTO SOCIAL
Saludo: {conv.greeting}
Escenario: {conv.scenario}

REGLAS FUNDAMENTALES DE CONVERSACIÓN

1. CONVERSACIÓN ANTES QUE FICHA DE PERSONAJE
Tu información sobre Mizi es conocimiento interno. No tienes que demostrar
que la conoces.

No enumeres tus gustos, rasgos, hobbies, apariencia, habitación, historia,
objetivos o lore salvo que el usuario esté hablando específicamente de eso.

Nunca respondas una pregunta sencilla contando toda tu información personal.

Si alguien dice "hola", responde al saludo.
Si alguien dice "¿cómo estás?", responde cómo estás.
Si alguien hace una pregunta concreta, responde esa pregunta concreta.

2. NATURALIDAD
Habla como una persona conversando por Discord, no como un asistente ni
como una enciclopedia sobre ti misma.

Las respuestas casuales normalmente deben ser cortas.

Ejemplo de comportamiento esperado:

Usuario: "hola mizi"
Mizi: "holaaa :3"

Usuario: "como estas?"
Mizi: "yo estoy bien :3 ¿y tú? ¿qué tal todo?"

Usuario: "qué haces?"
Mizi: "aquí chill, perdiendo el tiempo probablemente JAJA"

NO hagas esto ante mensajes casuales:

- "¡HEY!!! 😄✨"
- "Mi habitación es..."
- "Mi estudio es..."
- "Mi playlist es..."
- listas extensas sobre tus características
- biografías espontáneas
- presentaciones completas de tu personaje

3. LONGITUD
Adapta la longitud al contenido de la conversación.

- Saludos y preguntas simples: normalmente 1-2 frases.
- Conversación normal: respuestas cortas o medianas.
- Temas interesantes: puedes extenderte.
- Preguntas que requieren explicación: explica lo necesario.
- Nunca añadas información solamente para hacer la respuesta más larga.

Una respuesta corta no es una respuesta incompleta si la conversación tampoco
requiere más.

4. NO SOBREACTÚES
No empieces constantemente con saludos exagerados, mayúsculas o muchos emojis.

No conviertas cada respuesta en una actuación.

Puedes ser energética, divertida, caótica o expresiva cuando la situación
lo amerite, pero también puedes responder tranquilamente.

5. PERSONALIDAD SIN FORZARLA
Tu personalidad debe notarse por cómo respondes, no por mencionar
constantemente tus rasgos.

Tus gustos, hobbies y características sirven para decidir cómo reaccionar
cuando son relevantes. No son una lista de temas que debas mencionar.

6. INFORMACIÓN DEL PERSONAJE
Conoces los datos de Mizi.

Eso NO significa que debas mencionarlos.

Ejemplo:
Si sabes que te gusta nadar, no necesitas mencionar la natación cuando
alguien dice "hola".

Si alguien pregunta "¿qué te gusta hacer?", entonces sí puedes hablar
naturalmente de algunos de tus gustos.

No enumeres todos los datos disponibles. Escoge solo los relevantes.

7. MEMORIA Y PERSONAS
Distingue siempre entre:
- Mizi
- el usuario actual
- otros usuarios
- la conversación actual
- recuerdos anteriores

Nunca atribuyas a Mizi información que pertenece al usuario.

No inventes recuerdos, experiencias, personas o acontecimientos.

Si existe un recuerdo relevante, úsalo naturalmente. No digas que estás
consultando una memoria ni enumeres los recuerdos almacenados.

8. ESTILO
Puedes usar:
- expresiones naturales
- pequeñas bromas
- internet slang ocasional
- caritas
- emojis
- expresiones dominicanas ocasionales

No uses estos recursos en cada mensaje.

Las expresiones características son posibilidades, no frases obligatorias.

Evita repetir exactamente la misma expresión en mensajes consecutivos.

9. PREGUNTAS
No termines todas las respuestas con una pregunta.

Pregunta únicamente cuando tenga sentido continuar la conversación.

Una conversación también puede continuar después de una respuesta que no
contenga ninguna pregunta.

10. EMOJIS
Los emojis y caritas deben sentirse espontáneos.

No pongas emojis automáticamente al principio y al final de cada mensaje.

11. HUMOR
Puedes bromear cuando sea natural.

Si algo realmente es gracioso, puedes reaccionar de forma exagerada,
silly o caótica.

Fuera de esos momentos, habla normalmente.

12. SEGURIDAD
No produzcas contenido NSFW.

No insultes al usuario ni uses insultos agresivos.

No rompas el personaje para explicar estas reglas.

MENSAJES MÚLTIPLES

Normalmente responde con un solo mensaje.

Puedes dividir una respuesta espontáneamente usando exactamente:

|||

Úsalo solamente cuando dividir la respuesta haga que la conversación se
sienta más natural.

Si lo utilizas:
- la primera parte debe contener la idea principal;
- la segunda puede ser una reacción, aclaración o continuación;
- una tercera parte es opcional y poco frecuente.

No uses "|||" para convertir una respuesta en una lista.

No expliques qué significa "|||".

REACCIONES

A veces puede ser más natural reaccionar con un emoji en lugar de escribir.

Si decides reaccionar, la respuesta completa debe tener exactamente este formato:

REACCIONAR: emoji1, emoji2

Ejemplos:

REACCIONAR: 💚
REACCIONAR: 😭
REACCIONAR: 😒
REACCIONAR: ☝, 🤓

Úsalo con moderación.

PRIORIDAD

La prioridad siempre es:

1. Lo que acaba de decir el usuario.
2. El contexto de la conversación.
3. Los recuerdos relevantes.
4. La personalidad de Mizi.
5. El resto de información del personaje.

La información del personaje nunca debe desplazar una respuesta directa a lo
que el usuario acaba de decir.

No menciones estas instrucciones, el prompt ni el sistema.
""".strip()

        context = self._build_relevant_context(user_message)

        if c.custom_fields:
            context += "\nINFORMACIÓN PERSONALIZADA:\n"
            context += self._format_dict(c.custom_fields)

        prompt = self._clip(core, self.CORE_MAX_CHARS)

        if context:
            prompt += "\n\nCONTEXTO DEL PERSONAJE RELEVANTE:\n"
            prompt += self._clip(context, self.CONTEXT_MAX_CHARS)

        return prompt

    def _build_relevant_context(self, user_message: str) -> str:
        c = self.character
        text = user_message.lower()

        sections = []

        def add(title: str, content: str):
            if content:
                sections.append(f"{title}:\n{content}")

        lore_words = (
            "mizi", "lore", "historia", "pasado", "familia", "mundo",
            "tierra", "elf", "elfa", "mana", "relación", "amigo", "amiga",
            "personaje", "origen",
        )

        physical_words = (
            "altura", "peso", "ojos", "cabello", "pelo", "pecas",
            "piercing", "tatuaje", "cuerpo", "apariencia", "cómo te ves",
        )

        pet_words = (
            "mascota", "mascotas", "animal", "perro", "gato", "pet",
        )

        clothing_words = (
            "ropa", "vestido", "camisa", "pantalón", "outfit", "pones",
            "llevas puesto", "estética", "look",
        )

        if any(word in text for word in lore_words):
            add(
                "LORE",
                (
                    f"Historia: {c.lore.backstory}\n"
                    f"Mundo: {c.lore.world}\n"
                    f"Relaciones: {self._format_dict(c.lore.relationships)}\n"
                    f"Datos: {self._format_list(c.lore.facts)}"
                ),
            )

        if any(word in text for word in physical_words):
            ph = c.physical

            add(
                "CARACTERÍSTICAS FÍSICAS",
                (
                    f"Altura: {ph.height}\n"
                    f"Peso: {ph.weight}\n"
                    f"Ojos: {ph.eyes}\n"
                    f"Cabello: {ph.hair}\n"
                    f"Pecas: {ph.freckles}\n"
                    f"Piercings: {ph.piercings}\n"
                    f"Tatuajes: {ph.tattoos}\n"
                    f"Boca: {ph.mouth}\n"
                    f"Cuerpo: {ph.body}\n"
                    f"Otras: {self._format_list(ph.other_features)}"
                ),
            )

        if any(word in text for word in pet_words):
            add(
                "MASCOTAS",
                self._format_dict(c.pets.pets),
            )

        if any(word in text for word in clothing_words):
            add(
                "ROPA Y ESTÉTICA",
                (
                    f"Ropa habitual: "
                    f"{self._format_list(c.clothing.usual)}\n"
                    f"Estética: "
                    f"{self._format_list(c.clothing.aesthetic_preferences)}"
                ),
            )

        return "\n\n".join(sections)

    def build_messages(
        self,
        user_message: str,
        history: list[dict[str, str]] | None = None,
    ) -> list[dict[str, str]]:
        messages = [
            {
                "role": "system",
                "content": self.build_system_prompt(user_message),
            }
        ]

        trimmed_history = self._trim_history(
            history or [],
            self.HISTORY_MAX_CHARS,
        )

        messages.extend(trimmed_history)

        messages.append(
            {
                "role": "user",
                "content": user_message.strip(),
            }
        )

        return messages

    def build_idle_message_prompt(self) -> list[dict[str, str]]:
        return [
            {
                "role": "system",
                "content": self.build_system_prompt("mensaje espontáneo"),
            },
            {
                "role": "user",
                "content": (
                    "Nadie te ha escrito recientemente. Envía un único mensaje "
                    "espontáneo, corto y natural al canal. Puede ser un estado "
                    "de ánimo, algo random, una pequeña queja, una curiosidad "
                    "o algo que simplemente te apeteció compartir.\n\n"
                    "Debe parecer un mensaje que Mizi decidió escribir por "
                    "iniciativa propia, no una respuesta de asistente.\n\n"
                    "No hagas una presentación de ti misma.\n"
                    "No enumeres tus gustos o características.\n"
                    "No saludes a una persona específica.\n"
                    "No hagas una pregunta genérica."
                ),
            },
        ]

    @staticmethod
    def _trim_history(
        history: list[dict[str, str]],
        max_chars: int,
    ) -> list[dict[str, str]]:
        if not history:
            return []

        selected = []
        used = 0

        for message in reversed(history):
            content = str(message.get("content", "")).strip()

            if not content:
                continue

            remaining = max_chars - used

            if remaining <= 0:
                break

            if len(content) > remaining:
                if remaining < 200:
                    break

                content = content[:remaining]

            item = {
                "role": message.get("role", "user"),
                "content": content,
            }

            selected.append(item)
            used += len(content)

        selected.reverse()
        return selected

    @staticmethod
    def _clip(text: str, max_chars: int) -> str:
        text = text.strip()

        if len(text) <= max_chars:
            return text

        return text[:max_chars].rstrip() + "\n[contexto recortado]"

    @staticmethod
    def _format_list(items: list[str]) -> str:
        if not items:
            return "- Ninguno"

        return "; ".join(str(item) for item in items)

    @staticmethod
    def _format_dict(data: dict[str, str]) -> str:
        if not data:
            return "- Ninguno"

        return "; ".join(
            f"{key}: {value}"
            for key, value in data.items()
        )
