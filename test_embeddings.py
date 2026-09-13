from services.bedrock_embeddings import generate_embedding


text = """
Urban Flex está fabricado en España,
utiliza piel y dispone de plantilla extraíble.
"""


embedding = generate_embedding(text)


print("Texto:")
print(text)

print("\nDimensión del embedding:")
print(len(embedding))

print("\nPrimeros 10 valores:")
print(embedding[:10])