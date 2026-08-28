from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

from websignal.models import NormalizedObservation


@dataclass
class StoredObservation:
    id: int
    data: NormalizedObservation


class MemoryRepository:
    def __init__(self) -> None:
        self._next_id = 1
        self._by_fp: dict[str, StoredObservation] = {}
        self._by_domain: dict[str, list[StoredObservation]] = defaultdict(list)
        self._changes: dict[str, list[dict]] = defaultdict(list)

    def ingest(self, observation: NormalizedObservation) -> tuple[bool, int]:
        if observation.fingerprint in self._by_fp:
            return False, 0
        previous = self._by_domain[observation.domain][-1].data if self._by_domain[observation.domain] else None
        stored = StoredObservation(self._next_id, observation)
        self._next_id += 1
        self._by_fp[observation.fingerprint] = stored
        self._by_domain[observation.domain].append(stored)
        self._by_domain[observation.domain].sort(key=lambda x: x.data.fetched_at)
        changes = 0
        if previous is not None:
            old = set(previous.technologies)
            new = set(observation.technologies)
            for value in sorted(new - old):
                self._changes[observation.domain].append({"event_type": "technology_added", "value": value, "observed_at": observation.fetched_at})
                changes += 1
            for value in sorted(old - new):
                self._changes[observation.domain].append({"event_type": "technology_removed", "value": value, "observed_at": observation.fetched_at})
                changes += 1
        return True, changes

    def list_companies(self, technology: str | None, offset: int, limit: int) -> list[dict]:
        rows = []
        for domain, items in self._by_domain.items():
            latest = items[-1].data
            if technology and technology not in latest.technologies:
                continue
            rows.append(self._company_dict(domain, items))
        rows.sort(key=lambda x: x["domain"] )
        return rows[offset:offset + limit]

    def get_company(self, domain: str) -> dict | None:
        items = self._by_domain.get(domain)
        return None if not items else self._company_dict(domain, items)

    def history(self, domain: str) -> list[dict]:
        return [dict(x) for x in self._changes.get(domain, [])]

    def stats(self) -> dict:
        tech_counts: dict[str, int] = defaultdict(int)
        for items in self._by_domain.values():
            for tech in items[-1].data.technologies:
                tech_counts[tech] += 1
        return {
            "companies": len(self._by_domain),
            "observations": len(self._by_fp),
            "change_events": sum(len(v) for v in self._changes.values()),
            "top_technologies": sorted(tech_counts.items(), key=lambda x: (-x[1], x[0]))[:10],
        }

    @staticmethod
    def _company_dict(domain: str, items: list[StoredObservation]) -> dict:
        latest = items[-1].data
        return {
            "domain": domain,
            "company_name": latest.company_name,
            "last_seen_at": latest.fetched_at,
            "latest_url": latest.canonical_url,
            "technologies": list(latest.technologies),
            "observation_count": len(items),
        }
