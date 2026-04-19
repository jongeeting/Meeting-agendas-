"""Query upcoming ZBA hearings and sheriff sales from BPN's Postgres.

Why this module exists:
  The Meeting Agendas Digest used to rely on scraping phila.gov and Legistar
  for ZBA agendas. That scraper was disabled because ZBA's page uses a
  JavaScript calendar that resists static scraping (config.yaml note).

  BPN's nightly pipeline already pulls ZBA appeals (with scheduled_date) and
  sheriff sales (with event_date_dt) into Postgres. Querying that directly
  bypasses the scraper entirely, stays in sync with the Carto source of truth,
  and lets us cross-link every item to its parcel page on map.buildphillynow.org.

Connection:
  Reads from `BPN_POSTGRES` environment variable — same connection string the
  BPN pipeline uses. Read-only queries with a short statement timeout.

Usage:
  from bpn_upcoming_events import fetch_upcoming_zba, fetch_upcoming_sheriff_sales
  hearings = fetch_upcoming_zba(days_ahead=7)
  sales = fetch_upcoming_sheriff_sales(days_ahead=7)
"""

from __future__ import annotations

import os
from datetime import date, timedelta
from typing import Any

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError as e:
    raise ImportError(
        "psycopg2 is required for BPN data queries. "
        "Install with: pip install psycopg2-binary"
    ) from e


# Connection timeout — we'd rather fail fast than block the digest job
CONNECT_TIMEOUT_SECS = 10
# Statement timeout — cap how long any individual query can run
STATEMENT_TIMEOUT_MS = 30_000


def _connection_string() -> str:
    conn = os.getenv("BPN_POSTGRES")
    if not conn:
        raise RuntimeError(
            "BPN_POSTGRES environment variable must be set. "
            "See the BPN pipeline setup for connection-string format."
        )
    return conn


def _get_connection():
    """Open a read-only connection with sensible timeouts."""
    return psycopg2.connect(
        _connection_string(),
        connect_timeout=CONNECT_TIMEOUT_SECS,
        options=f"-c statement_timeout={STATEMENT_TIMEOUT_MS}",
    )


def fetch_upcoming_zba(
    days_ahead: int = 7,
    start_date: date | None = None,
) -> list[dict[str, Any]]:
    """Return upcoming ZBA hearings scheduled in the next `days_ahead` days.

    Joins parcel_event against the parcel table to enrich each row with an
    address, zoning, neighborhood, and council district for grouping and
    filtering in the digest template.

    Returns a list of dicts; empty list if BPN_POSTGRES is unreachable or no
    hearings fall in the window (not an error — just a quiet week).
    """
    start = start_date or date.today()
    end = start + timedelta(days=days_ahead)

    sql = """
        SELECT
            pe.id,
            pe.opa_number,
            pe.event_date_dt AS event_date,
            pe.scheduled_date,
            pe.appellant,
            pe.appeal_grounds,
            pe.status,
            pe.source_id AS case_number,
            COALESCE(p.address, pe.address) AS address,
            p.zoning,
            p.neighborhood,
            p.council_district
        FROM parcel_event pe
        LEFT JOIN parcel p ON p.opa_number = pe.opa_number
        WHERE pe.source_table = 'appeals'
          AND pe.scheduled_date IS NOT NULL
          AND pe.scheduled_date::date BETWEEN %(start)s AND %(end)s
        ORDER BY pe.scheduled_date::date ASC, p.neighborhood NULLS LAST
    """

    try:
        with _get_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, {"start": start, "end": end})
            return [dict(row) for row in cur.fetchall()]
    except psycopg2.Error as e:
        # Non-fatal: log and return empty so the digest can still ship with
        # whatever scraper data it has. A zero-ZBA week is a valid output.
        print(f"[bpn_upcoming_events] ZBA query failed: {e}")
        return []


def fetch_upcoming_sheriff_sales(
    days_ahead: int = 7,
    start_date: date | None = None,
) -> list[dict[str, Any]]:
    """Return upcoming sheriff sales listed in the next `days_ahead` days."""
    start = start_date or date.today()
    end = start + timedelta(days=days_ahead)

    sql = """
        SELECT
            pe.id,
            pe.opa_number,
            pe.event_date_dt AS event_date,
            pe.description,
            pe.source_id AS case_number,
            COALESCE(p.address, pe.address) AS address,
            p.zoning,
            p.neighborhood,
            p.council_district,
            p.market_value
        FROM parcel_event pe
        LEFT JOIN parcel p ON p.opa_number = pe.opa_number
        WHERE pe.source_table = 'sheriff_sales'
          AND pe.event_date_dt BETWEEN %(start)s AND %(end)s
        ORDER BY pe.event_date_dt ASC, p.neighborhood NULLS LAST
    """

    try:
        with _get_connection() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, {"start": start, "end": end})
            return [dict(row) for row in cur.fetchall()]
    except psycopg2.Error as e:
        print(f"[bpn_upcoming_events] Sheriff sales query failed: {e}")
        return []


def buildphillynow_parcel_url(opa_number: str | None) -> str | None:
    """Build a deep link to a parcel's BPN page. Returns None for empty opa."""
    if not opa_number:
        return None
    # Strip non-digits — matches the pattern BPN's /parcel/[parcelNumber] route uses
    clean = "".join(c for c in str(opa_number) if c.isdigit())
    if len(clean) < 5:
        return None
    return f"https://map.buildphillynow.org/parcel/{clean}"


def format_zba_section(hearings: list[dict[str, Any]]) -> str:
    """Render ZBA hearings as a markdown digest section.

    Groups by day so a multi-day week reads as a natural agenda. Caps items
    per day at 10 with an overflow line. Each hearing links to its parcel
    page on BPN for context (ownership, zoning, recent permits).
    """
    if not hearings:
        return "*No ZBA hearings scheduled this week.*"

    MAX_PER_DAY = 10
    lines: list[str] = []

    # Group by scheduled date
    by_day: dict[str, list[dict[str, Any]]] = {}
    for h in hearings:
        day = h.get("scheduled_date") or "Unscheduled"
        by_day.setdefault(str(day), []).append(h)

    for day, items in sorted(by_day.items()):
        lines.append(f"\n**{day}** ({len(items)} hearing{'s' if len(items) != 1 else ''})")
        shown = items[:MAX_PER_DAY]
        overflow = len(items) - len(shown)
        for h in shown:
            addr = h.get("address") or "Address unavailable"
            url = buildphillynow_parcel_url(h.get("opa_number"))
            bpn_link = f" ([details]({url}))" if url else ""
            nhood = h.get("neighborhood")
            nhood_suffix = f" — {nhood}" if nhood else ""
            grounds = h.get("appeal_grounds")
            # Trim appeal_grounds to the first clause; full text goes on BPN
            grounds_short = ""
            if grounds:
                first_sentence = grounds.split(".")[0].strip()
                # Also cap length to keep email rows scannable
                if len(first_sentence) > 140:
                    first_sentence = first_sentence[:137].rstrip() + "…"
                grounds_short = f" — {first_sentence}"
            lines.append(f"- {addr}{nhood_suffix}{bpn_link}{grounds_short}")
        if overflow > 0:
            lines.append(f"- *+ {overflow} more hearings this day*")

    return "\n".join(lines)


def format_sheriff_section(sales: list[dict[str, Any]]) -> str:
    """Render upcoming sheriff sales as a markdown digest section."""
    if not sales:
        return "*No sheriff sales scheduled this week.*"

    MAX_ITEMS = 20
    lines: list[str] = []
    shown = sales[:MAX_ITEMS]
    overflow = len(sales) - len(shown)

    for s in shown:
        addr = s.get("address") or "Address unavailable"
        url = buildphillynow_parcel_url(s.get("opa_number"))
        bpn_link = f" ([details]({url}))" if url else ""
        nhood = s.get("neighborhood")
        nhood_suffix = f" — {nhood}" if nhood else ""
        event_date = s.get("event_date")
        date_suffix = f" ({event_date})" if event_date else ""
        lines.append(f"- {addr}{nhood_suffix}{date_suffix}{bpn_link}")

    if overflow > 0:
        lines.append(f"- *+ {overflow} more sales scheduled this week*")

    return "\n".join(lines)
