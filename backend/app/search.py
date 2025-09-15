from typing import List
from sentence_transformers import SentenceTransformer

_model: SentenceTransformer | None = None

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    return _model

def generate_embedding(text: str) -> List[float]:
    model = get_model()
    return model.encode(text, normalize_embeddings=True).tolist()