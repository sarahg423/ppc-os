"""Parse CSV exports from Google Search Console.

Fallback path when the Search Console API isn't available. Users can
export performance data from GSC's web interface and drop CSVs into
data/exports/ for analysis.

GSC exports come in two flavors:
  1. Queries export — columns: Top queries, Clicks, Impressions, CTR, Position
  2. Pages export — columns: Top pages, Clicks, Impressions, CTR, Position
"""

import csv
from pathlib import Path
from typing import Optional

from ads_manager import get_project_root


def _export_dir() -> Path:
    return get_project_root() / "data" / "exports"


def parse_gsc_queries_export(filepath: str | Path) -> list[dict]:
    """Parse a GSC queries export CSV.

    GSC exports have varying column names depending on language/version.
    We normalize common variations.
    """
    rows = _parse_gsc_csv(filepath)
    queries = []
    for row in rows:
        query = (
            row.get("Top queries")
            or row.get("Query")
            or row.get("Search query")
            or row.get("Queries")
            or ""
        )
        if not query:
            continue
        queries.append({
            "query": query,
            "clicks": _to_int(row.get("Clicks", "")),
            "impressions": _to_int(row.get("Impressions", "")),
            "ctr": _to_pct(row.get("CTR", row.get("Click-through rate", ""))),
            "position": _to_float(row.get("Position", row.get("Average position", ""))),
        })
    return sorted(queries, key=lambda q: q.get("clicks") or 0, reverse=True)


def parse_gsc_pages_export(filepath: str | Path) -> list[dict]:
    """Parse a GSC pages export CSV."""
    rows = _parse_gsc_csv(filepath)
    pages = []
    for row in rows:
        page = (
            row.get("Top pages")
            or row.get("Page")
            or row.get("Pages")
            or row.get("URL")
            or ""
        )
        if not page:
            continue
        pages.append({
            "page": page,
            "clicks": _to_int(row.get("Clicks", "")),
            "impressions": _to_int(row.get("Impressions", "")),
            "ctr": _to_pct(row.get("CTR", row.get("Click-through rate", ""))),
            "position": _to_float(row.get("Position", row.get("Average position", ""))),
        })
    return sorted(pages, key=lambda p: p.get("clicks") or 0, reverse=True)


def list_gsc_exports() -> list[Path]:
    """List CSV files in exports/ that look like GSC exports.

    GSC exports typically have 'Queries', 'Pages', or 'Search' in the filename,
    or contain GSC-specific column headers.
    """
    export_dir = _export_dir()
    if not export_dir.exists():
        return []

    gsc_files = []
    for f in sorted(export_dir.glob("*.csv"), key=lambda p: p.stat().st_mtime, reverse=True):
        name_lower = f.name.lower()
        if any(hint in name_lower for hint in ["quer", "page", "search_console", "gsc", "organic"]):
            gsc_files.append(f)
            continue
        # Check headers for GSC-specific columns
        if _looks_like_gsc_export(f):
            gsc_files.append(f)

    return gsc_files


def _looks_like_gsc_export(filepath: Path) -> bool:
    """Peek at headers to see if this CSV looks like a GSC export."""
    try:
        with open(filepath, encoding="utf-8") as f:
            header = f.readline().lower()
        gsc_indicators = ["top queries", "top pages", "position", "average position"]
        return any(ind in header for ind in gsc_indicators)
    except (OSError, UnicodeDecodeError):
        return False


def _parse_gsc_csv(filepath: str | Path) -> list[dict]:
    """Parse a GSC CSV file, handling BOM and encoding variations."""
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"CSV not found: {filepath}")

    # GSC exports sometimes have a BOM
    for encoding in ["utf-8-sig", "utf-8", "latin-1"]:
        try:
            with open(filepath, encoding=encoding) as f:
                reader = csv.DictReader(f)
                return list(reader)
        except UnicodeDecodeError:
            continue

    raise ValueError(f"Could not decode {filepath} with any supported encoding")


def _to_float(val: str) -> Optional[float]:
    if not val:
        return None
    val = str(val).replace(",", "").replace("%", "").strip()
    try:
        return float(val)
    except ValueError:
        return None


def _to_int(val: str) -> Optional[int]:
    f = _to_float(val)
    return int(f) if f is not None else None


def _to_pct(val: str) -> Optional[float]:
    if not val:
        return None
    val = str(val).strip()
    if val.endswith("%"):
        f = _to_float(val.replace("%", ""))
        return f / 100 if f is not None else None
    f = _to_float(val)
    # GSC exports CTR as a decimal (e.g., 0.05) not a percentage
    return f
