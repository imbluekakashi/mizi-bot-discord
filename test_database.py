from database.database import Base, engine
from database.models import CharacterModel


Base.metadata.create_all(engine)

print("Base de datos creada correctamente.")
print("Tablas:", list(Base.metadata.tables.keys()))