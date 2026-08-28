from __future__ import annotations

from sqlalchemy import and_, create_engine, delete, func, insert, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import Engine

from websignal.models import NormalizedObservation
from websignal.normalization import normalize_technology
from .schema import change_events, companies, metadata, observations, technology_signals


class PostgresRepository:
    def __init__(self, database_url: str) -> None:
        self.engine: Engine = create_engine(database_url, pool_pre_ping=True)

    def create_schema(self) -> None:
        metadata.create_all(self.engine)

    def ingest(self, observation: NormalizedObservation) -> tuple[bool, int]:
        with self.engine.begin() as conn:
            exists = conn.scalar(select(observations.c.id).where(observations.c.fingerprint == observation.fingerprint))
            if exists is not None:
                return False, 0

            company_id = conn.scalar(select(companies.c.id).where(companies.c.domain == observation.domain))
            previous_tech: set[str] = set()
            if company_id is not None:
                previous_obs_id = conn.scalar(
                    select(observations.c.id)
                    .where(observations.c.company_id == company_id)
                    .order_by(observations.c.fetched_at.desc())
                    .limit(1)
                )
                if previous_obs_id is not None:
                    previous_tech = set(conn.scalars(select(technology_signals.c.technology).where(technology_signals.c.observation_id == previous_obs_id)))

            company_stmt = pg_insert(companies).values(
                domain=observation.domain, company_name=observation.company_name,
                first_seen_at=observation.fetched_at, last_seen_at=observation.fetched_at
            ).on_conflict_do_update(
                index_elements=[companies.c.domain],
                set_={
                    "company_name": func.coalesce(pg_insert(companies).excluded.company_name, companies.c.company_name),
                    "last_seen_at": func.greatest(companies.c.last_seen_at, pg_insert(companies).excluded.last_seen_at),
                },
            ).returning(companies.c.id)
            company_id = conn.scalar(company_stmt)

            raw_payload = observation.model_dump(mode="json")
            observation_id = conn.scalar(insert(observations).values(
                company_id=company_id, canonical_url=observation.canonical_url, fetched_at=observation.fetched_at,
                title=observation.title, body_text=observation.text, fingerprint=observation.fingerprint, raw_payload=raw_payload
            ).returning(observations.c.id))

            if observation.technologies:
                conn.execute(insert(technology_signals), [
                    {"observation_id": observation_id, "technology": tech} for tech in observation.technologies
                ])

            current = set(observation.technologies)
            event_rows = [
                {"company_id": company_id, "event_type": "technology_added", "value": v, "observed_at": observation.fetched_at}
                for v in sorted(current - previous_tech)
            ] if previous_tech else []
            if previous_tech:
                event_rows += [
                    {"company_id": company_id, "event_type": "technology_removed", "value": v, "observed_at": observation.fetched_at}
                    for v in sorted(previous_tech - current)
                ]
            if event_rows:
                conn.execute(insert(change_events), event_rows)
            return True, len(event_rows)

    def list_companies(self, technology: str | None, offset: int, limit: int) -> list[dict]:
        technology = normalize_technology(technology) if technology else None
        with self.engine.connect() as conn:
            latest = (
                select(
                    observations.c.company_id,
                    func.max(observations.c.fetched_at).label("max_fetched_at")
                ).group_by(observations.c.company_id).subquery()
            )
            latest_obs = (
                select(observations)
                .join(latest, and_(observations.c.company_id == latest.c.company_id, observations.c.fetched_at == latest.c.max_fetched_at))
                .subquery()
            )
            stmt = select(companies.c.domain, companies.c.company_name, companies.c.last_seen_at, latest_obs.c.id.label("obs_id"), latest_obs.c.canonical_url)
            stmt = stmt.join(latest_obs, latest_obs.c.company_id == companies.c.id)
            if technology:
                stmt = stmt.where(select(technology_signals.c.id).where(
                    and_(technology_signals.c.observation_id == latest_obs.c.id, technology_signals.c.technology == technology)
                ).exists())
            stmt = stmt.order_by(companies.c.domain).offset(offset).limit(limit)
            result = []
            for row in conn.execute(stmt).mappings():
                techs = list(conn.scalars(select(technology_signals.c.technology).where(technology_signals.c.observation_id == row["obs_id"]).order_by(technology_signals.c.technology)))
                result.append({
                    "domain": row["domain"], "company_name": row["company_name"], "last_seen_at": row["last_seen_at"],
                    "latest_url": row["canonical_url"], "technologies": techs,
                })
            return result

    def get_company(self, domain: str) -> dict | None:
        rows = self.list_companies(None, 0, 100000)
        return next((r for r in rows if r["domain"] == domain), None)

    def history(self, domain: str) -> list[dict]:
        with self.engine.connect() as conn:
            company_id = conn.scalar(select(companies.c.id).where(companies.c.domain == domain))
            if company_id is None:
                return []
            stmt = select(change_events.c.event_type, change_events.c.value, change_events.c.observed_at).where(
                change_events.c.company_id == company_id
            ).order_by(change_events.c.observed_at)
            return [dict(r) for r in conn.execute(stmt).mappings()]

    def stats(self) -> dict:
        with self.engine.connect() as conn:
            return {
                "companies": conn.scalar(select(func.count()).select_from(companies)) or 0,
                "observations": conn.scalar(select(func.count()).select_from(observations)) or 0,
                "change_events": conn.scalar(select(func.count()).select_from(change_events)) or 0,
            }
