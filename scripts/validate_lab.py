"""Additional invariants the starter's 42 tests do not cover. No network calls."""
import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bench import read_document, evaluate
from src.agent import KnowledgeBaseAgent
from src.chunking import RecursiveChunker, SentenceChunker, ChunkingStrategyComparator
from src.heading import HeadingChunker
from src.models import Document
from src.store import EmbeddingStore


def validate_corpus():
    directory = ROOT / "data/shopee-doi-tra-hoan-tien"
    docs = {}
    required = {"doc_id", "title", "source_url", "retrieved_at", "document_version", "audience", "category"}
    for path in sorted(directory.glob("*.md")):
        metadata, content = read_document(path)
        assert required <= metadata.keys(), path
        assert all(metadata[k] for k in required), path
        assert metadata["doc_id"] == path.stem, path
        assert metadata["audience"] in {"buyer", "seller", "both"}, path
        assert metadata["source_url"].startswith("https://help.shopee.vn/portal/4/article/"), path
        assert content.startswith("#"), path
        docs[path.stem] = (metadata, content)
        print(f"OK {path.name}: {len(content)} characters, {metadata['audience']}")
    assert 5 <= len(docs) <= 10
    assert len({m["audience"] for m, _ in docs.values()}) >= 2
    rows = list(csv.DictReader((directory / "sources.csv").open(encoding="utf-8", newline="")))
    assert sorted(row["doc_id"] for row in rows) == sorted(docs)
    for row in rows:
        metadata, _ = docs[row["doc_id"]]
        assert (ROOT / row["file_path"]).is_file()
        for key in ["source_url", "title", "retrieved_at", "document_version"]:
            assert row[key] == metadata[key]
        assert row["license_or_permission"]
    queries = json.loads((ROOT / "benchmark_queries.json").read_text(encoding="utf-8"))
    assert len(queries) == 5 and len({q["id"] for q in queries}) == 5
    assert any(q.get("requires_filter") and q["metadata_filter"] for q in queries)
    for q in queries:
        m, content = docs[q["gold_doc_id"]]
        assert all(p.casefold() in content.casefold() for p in q["evidence_phrases"]), q["id"]
        assert all(m.get(k) == v for k, v in (q.get("metadata_filter") or {}).items())
    print("OK manifest 1:1; metadata; five gold answers present; buyer/seller split")
    output = ROOT / "report/benchmark_all.json"
    if output.exists():
        results = json.loads(output.read_text(encoding="utf-8"))
        assert results["query_sha256"] == hashlib.sha256((ROOT / "benchmark_queries.json").read_bytes()).hexdigest()
        for run in results["runs"]:
            for filename, digest in run["corpus_sha256"].items():
                assert hashlib.sha256((directory / filename).read_bytes()).hexdigest() == digest
            q = next(q for q in run["queries"] if q.get("requires_filter"))
            assert all(r["metadata"]["audience"] == "seller" for r in q["top3"])
            assert [r["id"] for r in q["top3"]] != [r["id"] for r in q["without_filter"]["top3"]]
        print("OK saved hashes match current files; Q1 A/B changes candidates for all three strategies")


def validate_regressions():
    text = "Một câu.\nHai câu! Ba câu?"
    assert SentenceChunker(1).chunk(text) == ["Một câu.", "Hai câu!", "Ba câu?"]
    for separators in [None, [], ["\n\n"], [". ", " "]]:
        for text in ["", "a" * 1001, "a\n" * 501, "Một đoạn. Hai đoạn.\n\n" * 50]:
            chunks = RecursiveChunker(separators, 80).chunk(text)
            assert "".join(chunks) == text
            assert all(0 < len(c) <= 80 for c in chunks)
    assert len(RecursiveChunker(chunk_size=100).chunk("a\n" * 50)) == 1
    assert all(v["count"] == 0 for v in ChunkingStrategyComparator().compare("").values())
    chunks = HeadingChunker(80).chunk("## Điều 4\n" + "nội dung " * 60)
    assert len(chunks) > 1 and all(c.startswith("## Điều 4\n") and len(c) <= 80 for c in chunks)
    metadata = {"audience": "buyer", "nested": {"x": 1}}
    store = EmbeddingStore(embedding_fn=lambda t: [1.0, 0.0] if t != "low" else [0.0, 1.0])
    store.add_documents([Document("seller#0", "high", {"audience": "seller"}),
                         Document("buyer#0", "low", metadata), Document("buyer#1", "low", metadata)])
    metadata["nested"]["x"] = 9
    result = store.search_with_filter("query", 1, {"audience": "buyer"})
    assert len(result) == 1 and result[0]["metadata"]["doc_id"] == "buyer"
    assert result[0]["metadata"]["nested"]["x"] == 1 and "embedding" not in result[0]
    assert store.search("query", 3) == store.search_with_filter("query", 3, None)
    assert store.search("query", 0) == [] and store.search("query", -1) == []
    assert store.delete_document("buyer") and store.get_collection_size() == 1
    assert not store.delete_document("buyer")
    calls = []
    assert KnowledgeBaseAgent(EmbeddingStore(), lambda p: calls.append(p)).answer("x")
    assert not calls
    KnowledgeBaseAgent(store, lambda p: calls.append(p) or "ok").answer("query")
    assert "[1] source=seller; chunk=seller#0" in calls[0] and "CÂU HỎI:\nquery" in calls[0]
    q = {"gold_doc_id": "x", "evidence_phrases": ["answer"]}
    bad = [{"metadata": {"doc_id": "x"}, "content": "same topic but missing facts"}]
    assert evaluate(q, bad, "answer")["evidence_score"] == 0
    print("OK regressions: preserved text, merging, heading, prefilter, metadata isolation, delete, empty agent, evidence scoring")


if __name__ == "__main__":
    validate_corpus()
    validate_regressions()
