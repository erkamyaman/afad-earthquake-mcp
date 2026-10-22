import unicodedata
from datetime import datetime, timedelta, timezone
from typing import Annotated

import httpx
from fastmcp import FastMCP
from pydantic import Field

AFAD_URL = "https://deprem.afad.gov.tr/apiv2/event/filter"

mcp = FastMCP("AFAD Earthquake")


def _normalize(text: str) -> str:
    text = text.replace("ı", "i").replace("I", "i")
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(c for c in decomposed if not unicodedata.combining(c)).strip()


def _to_float(value: str | None) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except ValueError:
        return None


TURKEY_TZ = timezone(timedelta(hours=3))


def _local_time(value: str | None) -> str:
    try:
        utc = datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return value or "-"
    return utc.astimezone(TURKEY_TZ).strftime("%Y-%m-%d %H:%M:%S")


def _table(events: list[dict], title: str) -> str:
    if not events:
        return f"**{title}**\n\nNo earthquakes found."
    rows = [
        f"**{title}** ({len(events)} shown)",
        "",
        "| Time (TR, UTC+3) | Magnitude | Depth (km) | Location |",
        "|---|---|---|---|",
    ]
    for e in events:
        magnitude = _to_float(e.get("magnitude"))
        depth = _to_float(e.get("depth"))
        mag_text = f"{magnitude:.1f} {e.get('type') or ''}".strip() if magnitude is not None else "-"
        depth_text = f"{depth:.1f}" if depth is not None else "-"
        location = (e.get("location") or "-").replace("|", "/")
        rows.append(f"| {_local_time(e.get('date'))} | {mag_text} | {depth_text} | {location} |")
    return "\n".join(rows)


async def _fetch(since: timedelta, min_magnitude: float | None, limit: int | None) -> list[dict]:
    end = datetime.now(timezone.utc)
    params = {
        "start": (end - since).strftime("%Y-%m-%dT%H:%M:%S"),
        "end": end.strftime("%Y-%m-%dT%H:%M:%S"),
        "orderby": "timedesc",
        "format": "json",
    }
    if min_magnitude is not None:
        params["minmag"] = min_magnitude
    if limit is not None:
        params["limit"] = limit
    async with httpx.AsyncClient(follow_redirects=True, timeout=20) as client:
        response = await client.get(AFAD_URL, params=params)
        response.raise_for_status()
        return response.json()


@mcp.tool
async def last_earthquakes(
    hours: Annotated[int, Field(ge=1, le=720, description="How many hours back to search")] = 24,
    min_magnitude: Annotated[float | None, Field(ge=0, le=10, description="Only quakes at or above this magnitude")] = None,
    limit: Annotated[int, Field(ge=1, le=100, description="Maximum number of quakes to return")] = 10,
) -> str:
    """Latest earthquakes in and around Türkiye from AFAD, newest first, as a Markdown table. Times are Türkiye time (UTC+3)."""
    events = await _fetch(timedelta(hours=hours), min_magnitude, limit)
    return _table(events, f"Earthquakes in the last {hours} hours")


@mcp.tool
async def city_earthquakes(
    city: Annotated[str, Field(description="Turkish province name, e.g. İzmir, Istanbul, Malatya. Case and Turkish letters are ignored.")],
    days: Annotated[int, Field(ge=1, le=90, description="How many days back to search")] = 7,
    min_magnitude: Annotated[float | None, Field(ge=0, le=10, description="Only quakes at or above this magnitude")] = None,
    limit: Annotated[int, Field(ge=1, le=100, description="Maximum number of quakes to return")] = 20,
) -> str:
    """Recent earthquakes in one Turkish province from AFAD, newest first, as a Markdown table. Times are Türkiye time (UTC+3)."""
    target = _normalize(city)
    events = await _fetch(timedelta(days=days), min_magnitude, None)
    matches = [e for e in events if _normalize(e.get("province") or "") == target]
    name = matches[0]["province"] if matches else city
    return _table(matches[:limit], f"Earthquakes in {name} in the last {days} days")


def main() -> None:
    mcp.run()
