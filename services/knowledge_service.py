# services/knowledge_service.py

import hashlib

from datetime import datetime

from services.bedrock_embeddings import generate_embedding

from services.rag import (
    chunk_text,
    rank_chunks,
    build_rag_context,
    log_retrieved_chunks
)

from services.database import (
    create_knowledge_document,
    get_knowledge_document,
    update_knowledge_document,
    delete_knowledge_chunks,
    save_knowledge_chunk,
    get_knowledge_chunks
)


# ============================================================
# CONOCIMIENTO INICIAL DE LA PRÁCTICA
# ============================================================

DEFAULT_KNOWLEDGE_TITLE = "Guía de marca Nébula Shoes"

DEFAULT_KNOWLEDGE_CONTENT = """
Marca: Nébula Shoes

Tono de comunicación:
La comunicación debe ser profesional, cercana y clara.
Debe evitarse el uso de superlativos y afirmaciones exageradas.
No deben utilizarse expresiones como "el mejor del mercado".

Producto Urban Flex:
Urban Flex está fabricado en España.
Su material exterior es piel.
Dispone de plantilla extraíble.
Está disponible en color negro y marrón.

Producto City Walk:
City Walk está fabricado en Portugal.
Dispone de una suela ligera.
Está disponible en color azul y gris.

Campaña invierno 2026:
La campaña de invierno debe destacar la comodidad y el uso urbano.
No debe utilizarse el claim "impermeable".
La promoción de invierno es válida hasta el 31 de enero.

Claims permitidos:
Puede utilizarse "Fabricado en España" cuando corresponda al producto.
Puede utilizarse "Plantilla extraíble" cuando corresponda al producto.

Claims prohibidos:
No utilizar "el mejor del mercado".
No utilizar "100 % impermeable".
No utilizar "garantía de por vida".
"""


# ============================================================
# HASH DEL CONTENIDO
# ============================================================

def calculate_content_hash(
    content: str
) -> str:
    """
    Calcula una huella SHA-256 del contenido.

    Permite saber si el documento de conocimiento
    ha cambiado desde la última indexación.
    """

    return hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()


# ============================================================
# INDEXACIÓN
# ============================================================

def sync_knowledge(
    project_id: int
) -> None:
    """
    Crea o reindexa el conocimiento del proyecto.

    - Si no existe, lo crea.
    - Si existe y el hash no ha cambiado, no hace nada.
    - Si el contenido ha cambiado, elimina los chunks antiguos
      y genera nuevos embeddings con Titan.
    """

    current_hash = calculate_content_hash(
        DEFAULT_KNOWLEDGE_CONTENT
    )

    document = get_knowledge_document(
        project_id=project_id,
        title=DEFAULT_KNOWLEDGE_TITLE
    )

    # --------------------------------------------------------
    # Documento ya indexado y sin cambios
    # --------------------------------------------------------
    if (
        document
        and document["content_hash"] == current_hash
    ):
        print(
            f"[RAG] Conocimiento del proyecto {project_id} "
            "sin cambios."
        )
        return

    # --------------------------------------------------------
    # Documento nuevo
    # --------------------------------------------------------
    if document is None:
        print(
            f"[RAG] Creando conocimiento inicial "
            f"para el proyecto {project_id}..."
        )

        document_id = create_knowledge_document(
            project_id=project_id,
            title=DEFAULT_KNOWLEDGE_TITLE,
            content=DEFAULT_KNOWLEDGE_CONTENT,
            content_hash=current_hash,
            created_at=datetime.now().isoformat()
        )

    # --------------------------------------------------------
    # Documento existente pero modificado
    # --------------------------------------------------------
    else:
        print(
            f"[RAG] El conocimiento del proyecto {project_id} "
            "ha cambiado. Reindexando..."
        )

        document_id = document["id"]

        delete_knowledge_chunks(
            document_id=document_id
        )

        update_knowledge_document(
            document_id=document_id,
            content=DEFAULT_KNOWLEDGE_CONTENT,
            content_hash=current_hash,
            created_at=datetime.now().isoformat()
        )

    # --------------------------------------------------------
    # Chunking
    # --------------------------------------------------------
    chunks = chunk_text(
        DEFAULT_KNOWLEDGE_CONTENT
    )

    print(
        f"[RAG] Documento dividido en "
        f"{len(chunks)} chunks."
    )

    # --------------------------------------------------------
    # Embeddings con Titan
    # --------------------------------------------------------
    for index, chunk in enumerate(chunks):
        print(
            f"[RAG] Generando embedding "
            f"del chunk {index + 1}/{len(chunks)}..."
        )

        embedding = generate_embedding(
            chunk
        )

        save_knowledge_chunk(
            document_id=document_id,
            chunk_index=index,
            chunk_text=chunk,
            embedding=embedding
        )

    print(
        "[RAG] Conocimiento indexado correctamente."
    )


# ============================================================
# BÚSQUEDA SEMÁNTICA
# ============================================================

def search_knowledge(
    project_id: int,
    query: str,
    top_k: int = 3
) -> list[dict]:
    """
    Genera el embedding de la consulta y recupera
    los chunks semánticamente más similares.
    """

    if not query or not query.strip():
        return []

    chunks = get_knowledge_chunks(
        project_id
    )

    if not chunks:
        print(
            f"[RAG] No hay chunks disponibles "
            f"para el proyecto {project_id}."
        )
        return []

    query_embedding = generate_embedding(
        query.strip()
    )

    retrieved_chunks = rank_chunks(
        query_embedding=query_embedding,
        chunks=chunks,
        top_k=top_k
    )

    log_retrieved_chunks(
        query=query,
        retrieved_chunks=retrieved_chunks
    )

    return retrieved_chunks


# ============================================================
# CONTEXTO PARA CLAUDE
# ============================================================

def get_rag_context(
    project_id: int,
    query: str,
    top_k: int = 3
) -> str:
    """
    Recupera los chunks relevantes y construye
    el contexto que se añadirá al prompt de Claude.
    """

    retrieved_chunks = search_knowledge(
        project_id=project_id,
        query=query,
        top_k=top_k
    )

    context = build_rag_context(
        retrieved_chunks
    )

    print("\n[RAG] Contexto final enviado a Claude:")
    print(context)
    print()

    return context