"""Reproducible retrieval experiment. Default: Cuong's recursive strategy.

The offline extractive responder is a transparent baseline, NOT a generative LLM.
Evidence/answer markers are scoring inputs only and never enter retrieval/prompts.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from src.agent import KnowledgeBaseAgent
from src.chunking import FixedSizeChunker, RecursiveChunker
from src.embeddings import MockEmbedder, LocalEmbedder, OpenAIEmbedder, GeminiEmbedder
from src.heading import HeadingChunker
from src.models import Document
from src.store import EmbeddingStore

ROOT = Path(__file__).resolve().parent
DEFAULT_STRATEGY = "recursive"  # Cuong; Dat: fixed_size; Trang: heading.


def normalize(text):
    return " ".join(unicodedata.normalize("NFC", text).casefold().split())


def read_document(path):
    """Read this corpus's flat YAML scalar schema, including JSON quoted strings."""
    text = path.read_text(encoding="utf-8-sig")
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not match:
        raise ValueError(f"Missing frontmatter: {path}")
    metadata = {}
    for line in match.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, separator, value = line.partition(":")
        if not separator:
            raise ValueError(f"Invalid metadata line: {line}")
        value = value.strip()
        if value.startswith('"'):
            value = json.loads(value)
        elif value.startswith("'") and value.endswith("'"):
            value = value[1:-1].replace("''", "'")
        metadata[key.strip()] = value
    return metadata, text[match.end():].strip()


def make_chunker(strategy, size=500):
    return {
        "fixed_size": lambda: FixedSizeChunker(size, min(50, size - 1)),
        "recursive": lambda: RecursiveChunker(chunk_size=size),
        "heading": lambda: HeadingChunker(size),
    }[strategy]()


class CachedEmbedder:
    def __init__(self, provider):
        # An explicitly requested real backend fails visibly instead of silently
        # mixing mock vectors with real embeddings in a benchmark.
        factories = {"mock": MockEmbedder, "local": LocalEmbedder,
                     "openai": OpenAIEmbedder, "gemini": GeminiEmbedder}
        options = {}
        model = os.getenv({"local": "LOCAL_EMBEDDING_MODEL", "openai": "OPENAI_EMBEDDING_MODEL",
                           "gemini": "GEMINI_EMBEDDING_MODEL"}.get(provider, "UNUSED_MODEL"))
        if model and provider != "mock":
            options["model_name"] = model
        self.backend = factories[provider](**options)
        self.name = f"{provider}:{getattr(self.backend, 'model_name', 'md5-64-v1')}"
        self.directory = ROOT / ".cache" / "embeddings" / hashlib.sha256(self.name.encode()).hexdigest()[:16]
        self.directory.mkdir(parents=True, exist_ok=True)

    def __call__(self, text):
        path = self.directory / (hashlib.sha256(text.encode("utf-8")).hexdigest() + ".json")
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        vector = self.backend(text)
        # Store assumes unit vectors, including API backends.
        norm = sum(x * x for x in vector) ** 0.5
        vector = [x / norm for x in vector] if norm else vector
        path.write_text(json.dumps(vector), encoding="utf-8")
        return vector


class FilteredView:
    """Adapt the unchanged agent signature to the benchmark's metadata filter."""
    def __init__(self, store, metadata_filter):
        self.store, self.metadata_filter = store, metadata_filter

    def search(self, question, top_k=3):
        return self.store.search_with_filter(question, top_k, self.metadata_filter)


def extractive_responder(prompt):
    """Return two source paragraphs chosen only by lexical question overlap."""
    context, question = prompt.split("NGỮ CẢNH:\n", 1)[1].rsplit("\n\nCÂU HỎI:\n", 1)
    stop = {"và", "của", "có", "thì", "là", "cho", "được", "tôi", "những", "nào"}
    tokens = set(re.findall(r"\w+", normalize(question))) - stop
    candidates = []
    for number, body in re.findall(r"\[(\d+)\] source=.*?; chunk=.*?\n(.*?)(?=\n\n\[\d+\] source=|\Z)", context, re.S):
        for paragraph in body.split("\n\n"):
            paragraph = re.sub(r"(?m)^#{1,6} .*\n?", "", paragraph).strip()
            if not paragraph:
                continue
            overlap = len(tokens & set(re.findall(r"\w+", normalize(paragraph))))
            candidates.append((overlap, paragraph, number))
    candidates.sort(key=lambda item: item[0], reverse=True)
    selected = candidates[:2]
    return "\n".join(f"{p} [{n}]" for _, p, n in selected) if selected else "Không tìm thấy thông tin."


def evaluate(query, results, answer):
    phrases = [normalize(p) for p in query["evidence_phrases"]]
    gold_results = [(i, r) for i, r in enumerate(results, 1)
                    if r["metadata"]["doc_id"] == query["gold_doc_id"]]
    doc_rank = gold_results[0][0] if gold_results else None
    # Require every answer marker to coexist in one relevant chunk. Merely
    # finding the gold file, or combining unrelated fragments, is insufficient.
    evidence_ranks = [i for i, r in gold_results if all(p in normalize(r["content"]) for p in phrases)]
    evidence_rank = min(evidence_ranks) if evidence_ranks else None
    answer_marker_match = bool(evidence_rank) and all(p in normalize(answer) for p in phrases)
    evidence_score = 2 if evidence_rank == 1 else (1 if evidence_rank else 0)
    return {"doc_rank": doc_rank, "evidence_rank": evidence_rank,
            "doc_only_score": 2 if doc_rank == 1 else (1 if doc_rank else 0),
            "evidence_score": evidence_score, "answer_marker_match": answer_marker_match,
            "agent_correctness": "requires-human-review",
            "automatic_score": evidence_score if answer_marker_match else (1 if evidence_rank else 0)}


def run(strategy, directory, queries, embedder, size=500):
    documents, lengths, hashes = [], [], {}
    chunker = make_chunker(strategy, size)
    for path in sorted(directory.glob("*.md")):
        metadata, content = read_document(path)
        if metadata.get("doc_id") != path.stem:
            raise ValueError(f"doc_id mismatch: {path}")
        hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        for i, chunk in enumerate(chunker.chunk(content)):
            documents.append(Document(f"{path.stem}#{i}", chunk,
                                      {**metadata, "doc_id": path.stem, "source": path.as_posix(), "chunk_index": i}))
            lengths.append(len(chunk))
    if not documents:
        raise ValueError(f"No corpus documents in {directory}")
    store = EmbeddingStore(embedding_fn=embedder)
    store.add_documents(documents)
    output = {"strategy": strategy, "chunk_size": size, "count": len(documents),
              "avg_length": sum(lengths) / len(lengths), "corpus_sha256": hashes, "queries": []}
    for query in queries:
        filter_ = query.get("metadata_filter")
        results = store.search_with_filter(query["query"], 3, filter_)
        agent = KnowledgeBaseAgent(FilteredView(store, filter_), extractive_responder)
        answer = agent.answer(query["query"])
        entry = {**query, "top3": results, "agent_answer": answer, **evaluate(query, results, answer)}
        if query.get("requires_filter"):
            unfiltered = store.search(query["query"], 3)
            ab_answer = KnowledgeBaseAgent(store, extractive_responder).answer(query["query"])
            entry["without_filter"] = {"top3": unfiltered, "agent_answer": ab_answer,
                                        **evaluate(query, unfiltered, ab_answer)}
        output["queries"].append(entry)
    for field in ["doc_only_score", "evidence_score", "automatic_score"]:
        output[field] = sum(q[field] for q in output["queries"])
    return output


def render(result):
    lines = [f"Run UTC: {result['run_at']}", f"Embedding backend: {result['backend']}",
             "Agent: offline extractive baseline (not a generative LLM).",
             "Automatic marker scores need human answer review; mock scores do not measure semantics."]
    for trial in result["runs"]:
        lines += [f"\n=== {trial['strategy']} | {trial['count']} chunks | avg_length={trial['avg_length']:.2f} ==="]
        for q in trial["queries"]:
            lines += [f"\n{q['id']}: {q['query']}", f"filter={q.get('metadata_filter')}", f"Gold: {q['gold_answer']}"]
            variants = [("with query filter", q)]
            if "without_filter" in q:
                variants.append(("A/B WITHOUT FILTER", q["without_filter"]))
            for label, entry in variants:
                lines.append(label)
                for i, r in enumerate(entry["top3"], 1):
                    lines += [f" {i}. {r['id']} | doc_id={r['metadata']['doc_id']} | audience={r['metadata']['audience']} | score={r['score']:.6f}",
                              f"    source={r['metadata']['source_url']}", f"    {r['content']}"]
                lines += [f"Agent answer: {entry['agent_answer']}",
                          f"doc_rank={entry['doc_rank']}; evidence_rank={entry['evidence_rank']}; answer_marker_match={entry['answer_marker_match']}; "
                          f"doc_only={entry['doc_only_score']}; evidence={entry['evidence_score']}; automatic={entry['automatic_score']}"]
        lines.append(f"TOTAL doc_only={trial['doc_only_score']}/10; evidence={trial['evidence_score']}/10; automatic={trial['automatic_score']}/10")
    return "\n".join(line.rstrip() for line in lines) + "\n"


def main():
    load_dotenv(ROOT / ".env", override=False)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strategy", choices=["fixed_size", "recursive", "heading", "all"], default=DEFAULT_STRATEGY)
    parser.add_argument("--provider", choices=["mock", "local", "openai", "gemini"], default=os.getenv("EMBEDDING_PROVIDER", "mock"))
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data/shopee-tra-hang-hoan-tien")
    parser.add_argument("--chunk-size", type=int, default=500)
    parser.add_argument("--output", type=Path, default=ROOT / "ket_qua_benchmark.txt")
    args = parser.parse_args()
    if args.chunk_size <= 0:
        parser.error("chunk-size must be positive")
    queries = json.loads((ROOT / "benchmark_queries.json").read_text(encoding="utf-8"))
    if len(queries) != 5:
        raise ValueError("Exactly five shared queries are required")
    embedder = CachedEmbedder(args.provider)
    strategies = ["fixed_size", "recursive", "heading"] if args.strategy == "all" else [args.strategy]
    result = {"run_at": datetime.now(timezone.utc).isoformat(), "backend": embedder.name,
              "query_sha256": hashlib.sha256((ROOT / "benchmark_queries.json").read_bytes()).hexdigest(),
              "runs": [run(s, args.data_dir, queries, embedder, args.chunk_size) for s in strategies]}
    output = render(result)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output, encoding="utf-8")
    args.output.with_suffix(".json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
