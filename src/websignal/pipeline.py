from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

from pydantic import ValidationError

from .models import CrawlRecord, IngestStats
from .normalization import normalize_record
from .storage.base import Repository


class ETLPipeline:
    def __init__(self, repository: Repository, batch_size: int = 500) -> None:
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        self.repository = repository
        self.batch_size = batch_size

    def ingest_records(self, records: Iterable[dict]) -> IngestStats:
        stats = IngestStats()
        seen_domains: set[str] = set()
        for raw in records:
            stats.read += 1
            try:
                record = CrawlRecord.model_validate(raw)
                observation = normalize_record(record)
            except (ValidationError, ValueError, TypeError):
                stats.rejected += 1
                continue
            inserted, changes = self.repository.ingest(observation)
            seen_domains.add(observation.domain)
            if inserted:
                stats.inserted += 1
                stats.change_events += changes
            else:
                stats.duplicates += 1
        stats.companies = len(seen_domains)
        return stats

    def ingest_jsonl(self, path: str | Path) -> IngestStats:
        def rows():
            with Path(path).open("r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        yield {"url": ""}
        return self.ingest_records(rows())
