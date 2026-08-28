from __future__ import annotations

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, MetaData, String, Table, Text, Column, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB

metadata = MetaData()

companies = Table(
    "companies", metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column("domain", String(255), nullable=False, unique=True),
    Column("company_name", String(255)),
    Column("first_seen_at", DateTime(timezone=True), nullable=False),
    Column("last_seen_at", DateTime(timezone=True), nullable=False),
)

observations = Table(
    "observations", metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column("company_id", BigInteger, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
    Column("canonical_url", Text, nullable=False),
    Column("fetched_at", DateTime(timezone=True), nullable=False),
    Column("title", Text, nullable=False, server_default=""),
    Column("body_text", Text, nullable=False, server_default=""),
    Column("fingerprint", String(64), nullable=False, unique=True),
    Column("raw_payload", JSONB, nullable=False),
)

technology_signals = Table(
    "technology_signals", metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column("observation_id", BigInteger, ForeignKey("observations.id", ondelete="CASCADE"), nullable=False),
    Column("technology", String(120), nullable=False),
    UniqueConstraint("observation_id", "technology", name="uq_observation_technology"),
)

change_events = Table(
    "change_events", metadata,
    Column("id", BigInteger, primary_key=True, autoincrement=True),
    Column("company_id", BigInteger, ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
    Column("event_type", String(80), nullable=False),
    Column("value", String(255), nullable=False),
    Column("observed_at", DateTime(timezone=True), nullable=False),
)

Index("ix_companies_domain", companies.c.domain)
Index("ix_observations_company_fetched", observations.c.company_id, observations.c.fetched_at.desc())
Index("ix_observations_fetched", observations.c.fetched_at.desc())
Index("ix_technology_lookup", technology_signals.c.technology, technology_signals.c.observation_id)
Index("ix_change_events_company_time", change_events.c.company_id, change_events.c.observed_at.desc())
