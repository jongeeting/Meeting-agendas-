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

# Load .env if present — same pattern as meeting_tracker.py. Safe to call
# from anywhere in the process; dotenv is a no-op if no .env file exists
# or if the caller has already loaded it.
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    # dotenv is already in requirements.txt, but if somehow missing we
    # fall back to pure os.environ (caller must export BPN_POSTGRES).
    pass

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
            pe.unit_count,
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
            pe.unit_count,
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


def _unit_count_prefix(unit_count: Any) -> str:
    """Render `🏘️ 12 units` as a prefix when unit_count is meaningful.

    BPN's pipeline parses unit counts from permit descriptions and scope-of-work
    text (see pipeline/events/transformer.py). Surfacing this up front lets
    readers filter by development scale at a glance — "a 40-unit variance
    next door" is very different from a single-family shed addition.
    """
    try:
        n = int(unit_count) if unit_count is not None else 0
    except (TypeError, ValueError):
        return ""
    if n <= 0:
        return ""
    # Don't label single-unit items — too noisy, and most are just SFHs
    if n == 1:
        return ""
    return f"**🏘️ {n} units** · "


def format_zba_section(hearings: list[dict[str, Any]]) -> str:
    """Render ZBA hearings as a markdown digest section.

    Groups by day so a multi-day week reads as a natural agenda. Caps items
    per day at 10 with an overflow line. Each hearing:
    - Leads with unit count when available (most useful signal for readers)
    - Links to its BPN parcel page for full context
    - Shows full appeal grounds on an indented line below the header, so
      the header stays scannable but the detail is still there
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
        # Sort within a day: multi-unit projects first (most newsworthy),
        # then everything else. Null unit_counts go last in their bucket.
        items.sort(
            key=lambda h: (
                -(int(h.get("unit_count") or 0) if h.get("unit_count") else 0),
                (h.get("neighborhood") or "~"),
            )
        )
        lines.append(f"\n**{day}** ({len(items)} hearing{'s' if len(items) != 1 else ''})")
        shown = items[:MAX_PER_DAY]
        overflow = len(items) - len(shown)
        for h in shown:
            addr = h.get("address") or "Address unavailable"
            url = buildphillynow_parcel_url(h.get("opa_number"))
            bpn_link = f" ([details]({url}))" if url else ""
            nhood = h.get("neighborhood")
            nhood_suffix = f" — {nhood}" if nhood else ""
            unit_prefix = _unit_count_prefix(h.get("unit_count"))
            grounds = (h.get("appeal_grounds") or "").strip()

            # Header line stays scannable
            lines.append(f"- {unit_prefix}**{addr}**{nhood_suffix}{bpn_link}")
            # Full appeal grounds on an indented continuation line — readers
            # can skim headers and drop into grounds when something catches.
            if grounds:
                # Markdown requires a blank line or two-space indent for
                # continuations in a list. Use a two-space indent so the
                # grounds sit visually under the bullet.
                lines.append(f"  {grounds}")
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
        unit_prefix = _unit_count_prefix(s.get("unit_count"))
        event_date = s.get("event_date")
        date_suffix = f" ({event_date})" if event_date else ""
        description = (s.get("description") or "").strip()

        lines.append(f"- {unit_prefix}**{addr}**{nhood_suffix}{date_suffix}{bpn_link}")
        # Sheriff-sale description is typically "Opening bid: $X | Atty: Y"
        # — short and useful on a continuation line.
        if description:
            lines.append(f"  {description}")

    if overflow > 0:
        lines.append(f"- *+ {overflow} more sales scheduled this week*")

    return "\n".join(lines)
