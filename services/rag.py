from __future__ import annotations

from math import sqrt


# ============================================================
# CHUNKING
# ============================================================

def chunk_text(text: str) -> list[str]:
    """
    Divide el documento en bloques lógicos separados
    por líneas en blanco.

    Cada bloque se trata como un chunk independiente.
    """

    chunks = [
        block.strip()
        for block in text.split("\n\n")
        if block.strip()
    ]

    return chunks# ============================================================
# SIMILITUD VECTORIAL
# ============================================================

def cosine_similarity(
    vector_a: list[float],
    vector_b: list[float]
) -> float:
    """
    Calcula la similitud coseno entre dos embeddings.
    Devuelve un valor normalmente comprendido entre -1 y 1.
    Cuanto más próximo a 1, mayor similitud semántica.
    """

    if not vector_a or not vector_b:
        return 0.0

    if len(vector_a) != len(vector_b):
        raise ValueError(
            "Los vectores deben tener la misma dimensión."
        )

    dot_product = sum(
        a * b
        for a, b in zip(vector_a, vector_b)
    )

    norm_a = sqrt(
        sum(a * a for a in vector_a)
    )

    norm_b = sqrt(
        sum(b * b for b in vector_b)
    )

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot_product / (norm_a * norm_b)


# ============================================================
# RANKING DE CHUNKS
# ============================================================

def rank_chunks(
    query_embedding: list[float],
    chunks: list[dict],
    top_k: int = 3,
    min_score: float = 0.60
) -> list[dict]:

    ranked_chunks = []

    for chunk in chunks:
        embedding = chunk.get("embedding")

        if not embedding:
            continue

        score = cosine_similarity(
            query_embedding,
            embedding
        )

        if score >= min_score:
            ranked_chunks.append({
                **chunk,
                "score": score
            })

    ranked_chunks.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return ranked_chunks[:top_k]


# ============================================================
# CONSTRUCCIÓN DE CONTEXTO
# ============================================================

def build_rag_context(
    retrieved_chunks: list[dict]
) -> str:
    """
    Construye el texto que se añadirá al prompt de Claude
    a partir de los chunks recuperados.
    """

    if not retrieved_chunks:
        return ""

    parts = []

    for index, chunk in enumerate(
        retrieved_chunks,
        start=1
    ):
        chunk_text = chunk["chunk_text"].strip()

        parts.append(
            f"[Fragmento {index}]\n{chunk_text}"
        )

    return "\n\n".join(parts)


# ============================================================
# LOG DE DESARROLLO
# ============================================================

def log_retrieved_chunks(
    query: str,
    retrieved_chunks: list[dict]
) -> None:
    """
    Muestra en consola qué fragmentos ha recuperado el RAG.
    Útil para validar el funcionamiento durante la práctica.
    """

    print("\n" + "=" * 70)
    print("[RAG] Consulta")
    print(query)

    if not retrieved_chunks:
        print("\n[RAG] No se han recuperado fragmentos.")
        print("=" * 70 + "\n")
        return

    print("\n[RAG] Fragmentos recuperados:")

    for index, chunk in enumerate(
        retrieved_chunks,
        start=1
    ):
        score = chunk.get("score", 0.0)

        print(
            f"\n{index}. "
            f"score={score:.4f}"
        )

        print(chunk["chunk_text"])

    print("=" * 70 + "\n")