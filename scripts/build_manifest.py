"""Rebuild the one-to-one inventory from the reviewed corpus metadata."""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from bench import read_document

directory = ROOT / "data/shopee-tra-hang-hoan-tien"
fields = ["doc_id", "file_path", "title", "source_url", "retrieved_at", "document_version", "license_or_permission"]
with (directory / "sources.csv").open("w", encoding="utf-8", newline="") as output:
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for path in sorted(directory.glob("*.md")):
        metadata, _ = read_document(path)
        row = {key: metadata[key] for key in fields if key in metadata}
        row["file_path"] = path.relative_to(ROOT).as_posix()
        row["license_or_permission"] = "public-source; original factual summary for education; no open licence claimed"
        writer.writerow(row)
