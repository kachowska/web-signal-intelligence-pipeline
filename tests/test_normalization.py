from datetime import datetime, timezone

import pytest

from websignal.models import CrawlRecord
from websignal.normalization import canonicalize_url, normalize_record, normalize_technology


def test_canonicalize_url_removes_tracking_and_www():
    assert canonicalize_url("http://www.Example.com/a//b/?utm_source=x&z=2&a=1#frag") == "https://example.com/a/b?a=1&z=2"

def test_invalid_domain_rejected():
    with pytest.raises(ValueError):
        canonicalize_url("localhost/path")

def test_technology_aliases():
    assert normalize_technology("Postgres") == "postgresql"
    assert normalize_technology("Python3") == "python"

def test_fingerprint_is_deterministic():
    r = CrawlRecord(url="https://example.com", fetched_at=datetime(2026,1,1,tzinfo=timezone.utc), technologies=["Python", "Postgres"])
    assert normalize_record(r).fingerprint == normalize_record(r).fingerprint
