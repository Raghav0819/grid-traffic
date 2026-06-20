"""
MV Act RAG — Ingest, embed, store, and retrieve Motor Vehicles Act sections.

Pipeline:
  1. Load corpus from mv_act_corpus.py
  2. Chunk section-wise (one chunk = one legal section — natural legal boundary)
  3. Embed with sentence-transformers (all-MiniLM-L6-v2, lightweight + fast)
  4. Store in ChromaDB (persisted locally at ./mv_act_chroma/)
  5. retrieve(violation_key) -> returns the matching legal section dict

Run once to build the index:
  python mv_act_rag.py --build

Then the app calls retrieve() on every challan generation.
"""

import os
import argparse
import chromadb
from chromadb.utils import embedding_functions

from mv_act_corpus import CORPUS

# ── paths ──────────────────────────────────────────────────────────────────
CHROMA_PATH      = "mv_act_chroma"
COLLECTION_NAME  = "mv_act_sections"
EMBED_MODEL      = "all-MiniLM-L6-v2"   # fast, lightweight, good for legal text

# ── embedding function ─────────────────────────────────────────────────────
def _get_embed_fn():
    return embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBED_MODEL
    )

# ── ChromaDB client ────────────────────────────────────────────────────────
def _get_collection(readonly=True):
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    col = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=_get_embed_fn(),
        metadata={"hnsw:space": "cosine"},
    )
    return col

# ── build index ────────────────────────────────────────────────────────────
def build_index():
    """
    Chunk the corpus section-wise and upsert into ChromaDB.
    Each document = full_text of one section.
    Metadata = everything else (section no, violation key, fine, etc.)
    """
    col = _get_collection()

    ids, docs, metas = [], [], []
    for entry in CORPUS:
        doc_id = f"sec_{entry['section']}"
        # combine full_text + keywords into one rich document string for embedding
        keyword_str = " ".join(entry.get("keywords", []))
        document    = f"{entry['full_text']}\n\nKeywords: {keyword_str}"

        meta = {
            "section":         entry["section"],
            "title":           entry["title"],
            "violation":       entry.get("violation") or "",
            "fine_inr":        entry.get("fine_inr") or 0,
            "imprisonment":    entry.get("imprisonment") or "",
            "disqualification":entry.get("disqualification") or "",
            "compoundable":    str(entry.get("compoundable", False)),
        }
        ids.append(doc_id)
        docs.append(document)
        metas.append(meta)

    col.upsert(ids=ids, documents=docs, metadatas=metas)
    print(f"[RAG] Index built: {len(ids)} sections stored in '{CHROMA_PATH}'")
    return len(ids)

# ── retrieve ───────────────────────────────────────────────────────────────
def retrieve(violation_key: str, n_results: int = 2) -> list[dict]:
    """
    Retrieve the most relevant legal sections for a given violation.

    Args:
        violation_key : e.g. "no_helmet" or "triple_riding"
        n_results     : number of sections to return (default 2)

    Returns:
        list of dicts, each containing:
            section, title, fine_inr, disqualification,
            compoundable, full_text (trimmed), score
    """
    if not os.path.exists(CHROMA_PATH):
        raise RuntimeError(
            "RAG index not built yet. Run: python mv_act_rag.py --build"
        )

    col = _get_collection()

    # query string: combine violation key with natural language
    query_map = {
        "no_helmet":     "penalty for not wearing helmet riding without helmet section 194D",
        "triple_riding": "triple riding more than one pillion motorcycle penalty section 194C",
    }
    query = query_map.get(
        violation_key,
        f"penalty for {violation_key.replace('_', ' ')} motor vehicle act fine"
    )

    results = col.query(
        query_texts=[query],
        n_results=min(n_results, len(CORPUS)),
        include=["documents", "metadatas", "distances"],
    )

    hits = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        hits.append({
            "section":         meta["section"],
            "title":           meta["title"],
            "fine_inr":        int(meta["fine_inr"]),
            "disqualification":meta["disqualification"],
            "imprisonment":    meta["imprisonment"],
            "compoundable":    meta["compoundable"] == "True",
            "full_text":       doc.split("\n\nKeywords:")[0].strip(),
            "score":           round(1 - float(dist), 3),  # cosine sim (higher = better)
        })
    return hits


def retrieve_all_for_violations(violations: list[str]) -> dict[str, dict]:
    """
    Retrieve legal info for a list of violation keys.
    Returns dict: {violation_key: best_hit}
    """
    out = {}
    for v in violations:
        hits = retrieve(v, n_results=1)
        out[v] = hits[0] if hits else None
    return out


# ── CLI: python mv_act_rag.py --build ─────────────────────────────────────
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true",
                    help="Build/rebuild the ChromaDB index from corpus")
    ap.add_argument("--query", type=str, default=None,
                    help="Test retrieval, e.g. --query no_helmet")
    args = ap.parse_args()

    if args.build:
        n = build_index()
        print(f"Done. {n} sections indexed.")

    if args.query:
        hits = retrieve(args.query)
        for h in hits:
            print(f"\nSection {h['section']}: {h['title']}")
            print(f"  Fine        : ₹{h['fine_inr']}")
            print(f"  Disqualify  : {h['disqualification'] or 'None'}")
            print(f"  Compoundable: {h['compoundable']}")
            print(f"  Score       : {h['score']}")
            print(f"  Text preview: {h['full_text'][:200]}...")