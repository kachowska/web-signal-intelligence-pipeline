from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator


class CrawlRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str
    fetched_at: datetime
    company_name: str | None = None
    title: str = ""
    text: str = ""
    technologies: list[str] = Field(default_factory=list)

    @field_validator("url")
    @classmethod
    def url_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("url must not be blank")
        return value.strip()


class NormalizedObservation(BaseModel):
    domain: str
    canonical_url: str
    fetched_at: datetime
    company_name: str | None
    title: str
    text: str
    technologies: tuple[str, ...]
    fingerprint: str


class IngestStats(BaseModel):
    read: int = 0
    inserted: int = 0
    duplicates: int = 0
    rejected: int = 0
    companies: int = 0
    change_events: int = 0
