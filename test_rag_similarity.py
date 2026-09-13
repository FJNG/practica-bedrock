from services.bedrock_embeddings import generate_embedding
from services.rag import cosine_similarity


query = "Quiero información sobre los mocasines Urban Flex"

urban_flex = """
Producto Urban Flex:
Fabricado en España.
Material exterior de piel.
Plantilla extraíble.
Disponible en negro y marrón.
"""

city_walk = """
Producto City Walk:
Fabricado en Portugal.
Suela ligera.
Disponible en azul y gris.
"""


query_embedding = generate_embedding(query)
urban_embedding = generate_embedding(urban_flex)
city_embedding = generate_embedding(city_walk)


urban_score = cosine_similarity(
    query_embedding,
    urban_embedding
)

city_score = cosine_similarity(
    query_embedding,
    city_embedding
)


print("Consulta:")
print(query)

print("\nSimilitud con Urban Flex:")
print(urban_score)

print("\nSimilitud con City Walk:")
print(city_score)