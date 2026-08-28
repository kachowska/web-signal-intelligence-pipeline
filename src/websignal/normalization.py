from __future__ import annotations

import hashlib
import json
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .models import CrawlRecord, NormalizedObservation

TRACKING_KEYS = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "gclid", "fbclid"}
TECH_ALIASES = {
    "postgres": "postgresql",
    "postgres sql": "postgresql",
    "postgresql": "postgresql",
    "python3": "python",
    "py": "python",
    "typescript": "typescript",
    "type script": "typescript",
    "js": "javascript",
    "nodejs": "node.js",
    "node js": "node.js",
    "reactjs": "react",
}


def canonicalize_url(url: str) -> str:
    raw = url.strip()
    if "://" not in raw:
        raw = "https://" + raw
    parts = urlsplit(raw)
    host = (parts.hostname or "").lower().strip(".")
    if host.startswith("www."):
        host = host[4:]
    if not host or "." not in host:
        raise ValueError(f"invalid host: {host!r}")
    port = parts.port
    netloc = host if port is None else f"{host}:{port}"
    path = re.sub(r"/{2,}", "/", parts.path or "/")
    if path != "/":
        path = path.rstrip("/")
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k.lower() not in TRACKING_KEYS]
    query.sort()
    return urlunsplit(("https", netloc, path, urlencode(query), ""))


def canonical_domain(url: str) -> str:
    return urlsplit(canonicalize_url(url)).hostname or ""


def normalize_technology(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9.+# -]+", "", value.lower()).strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    return TECH_ALIASES.get(cleaned, cleaned)


def normalize_record(record: CrawlRecord) -> NormalizedObservation:
    canonical_url = canonicalize_url(record.url)
    domain = urlsplit(canonical_url).hostname or ""
    technologies = tuple(sorted({normalize_technology(t) for t in record.technologies if normalize_technology(t)}))
    company_name = record.company_name.strip() if record.company_name and record.company_name.strip() else None
    title = " ".join(record.title.split())
    text = " ".join(record.text.split())
    payload = {
        "domain": domain,
        "url": canonical_url,
        "fetched_at": record.fetched_at.isoformat(),
        "company_name": company_name,
        "title": title,
        "text": text,
        "technologies": technologies,
    }
    fingerprint = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    return NormalizedObservation(
        domain=domain, canonical_url=canonical_url, fetched_at=record.fetched_at, company_name=company_name,
        title=title, text=text, technologies=technologies, fingerprint=fingerprint
    )
