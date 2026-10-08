"""Offline SQLite equivalent of export_customer_data.py + export_instrument_data.py.

Reads the verified local SQLite copy of PeCalHackathon2026 (read-only URI,
SELECT only) and writes the same `analysis/customers/*.json` extracts the
Member 1 snapshot builder consumes. Run this instead of the SQL Server
scripts when the lab network/ODBC driver is unavailable.

SQL Server semantics preserved: blank-customer exclusion, complete-month
windows, per-(customer,month) and per-(customer,group) aggregation,
MIN(Branche) industry mapping, deterministic SHA-256 IDs, raw instrument
UUIDs (the builder hashes those itself).

One deliberate difference, documented: SQL HASHBYTES hashes the NVARCHAR
(UTF-16LE) bytes while this script hashes UTF-8, so pseudonymous IDs
differ from a SQL-Server-produced extract. All joins inside this build
use one consistent hashing (this script), and every downstream artifact
shares its snapshot_id, so cross-extract consistency holds.

Usage:
  uv run python analysis/export_sqlite_offline.py --source /path/to/perschmann.sqlite
"""

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).parent / "customers"

HISTORY_START = "2024-01-01"
HISTORY_END = "2026-09-01"
GROUPS_START = "2025-09-01"
GROUPS_END = "2026-09-01"


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _nonblank(column: str) -> str:
    return f"({column} IS NOT NULL AND TRIM({column}) <> '')"


def _write_streamed(path: Path, rows) -> int:
    tmp = path.with_suffix(".json.tmp")
    count = 0
    with tmp.open("w") as output:
        output.write("[")
        for row in rows:
            if count:
                output.write(",")
            output.write(json.dumps(row, ensure_ascii=False))
            count += 1
            if count % 50000 == 0:
                print(path.name, count, flush=True)
        output.write("]")
    tmp.replace(path)
    print(path.name, "complete", count, flush=True)
    return count


def extract_monthly(conn: sqlite3.Connection):
    cur = conn.execute(
        """SELECT KUNDENNUMMER_SAP, SUBSTR(BEGINN,1,7) AS month,
                  COUNT(*) AS calibrations,
                  COUNT(DISTINCT MESSMITTEL_UUID) AS instruments,
                  COUNT(DISTINCT MESSMITTELGRUPPE) AS equipment_groups,
                  COUNT(DISTINCT MESSRAUM) AS labs
           FROM "dbo.KALIBRIERUNGEN"
           WHERE BEGINN >= ? AND BEGINN < ?
             AND """ + _nonblank("KUNDENNUMMER_SAP") + """
           GROUP BY KUNDENNUMMER_SAP, SUBSTR(BEGINN,1,7)
           ORDER BY KUNDENNUMMER_SAP, month""",
        (HISTORY_START, HISTORY_END),
    )
    for customer, month, cal, inst, groups, labs in cur:
        yield {
            "customer": _digest(customer),
            "month": month,
            "calibrations": cal,
            "instruments": inst,
            "equipment_groups": groups,
            "labs": labs,
        }


def extract_groups(conn: sqlite3.Connection):
    cur = conn.execute(
        """SELECT KUNDENNUMMER_SAP, COALESCE(MESSMITTELGRUPPE,'Unknown') AS equipment_group,
                  COUNT(*) AS calibrations
           FROM "dbo.KALIBRIERUNGEN"
           WHERE BEGINN >= ? AND BEGINN < ?
             AND """ + _nonblank("KUNDENNUMMER_SAP") + """
           GROUP BY KUNDENNUMMER_SAP, COALESCE(MESSMITTELGRUPPE,'Unknown')
           ORDER BY KUNDENNUMMER_SAP, equipment_group""",
        (GROUPS_START, GROUPS_END),
    )
    for customer, group, cal in cur:
        yield {"customer": _digest(customer), "equipment_group": group, "calibrations": cal}


def extract_industry(conn: sqlite3.Connection):
    branches: dict[str, list[str]] = {}
    for number, branche in conn.execute('SELECT KundenNr, Branche FROM "dbo.Kunde_Branche"'):
        if number is None:
            continue
        branches.setdefault(number, []).append(branche)
    industry = {number: sorted(set(values))[0] for number, values in branches.items()}
    customers = {
        row[0]
        for row in conn.execute(
            'SELECT DISTINCT KUNDENNUMMER_SAP FROM "dbo.KALIBRIERUNGEN" WHERE '
            + _nonblank("KUNDENNUMMER_SAP")
        )
    }
    for customer in sorted(customers):
        yield {"customer": _digest(customer), "industry": industry.get(customer, "Unknown")}
    duplicates = sum(1 for values in branches.values() if len(set(values)) > 1)
    (ROOT / "industry_duplicates.json").write_text(
        json.dumps([{"customers_with_conflicting_industry": duplicates}])
    )
    print("industry_duplicates", duplicates, flush=True)


def extract_instruments(conn: sqlite3.Connection):
    cur = conn.execute(
        """SELECT MESSMITTEL_UUID, KUNDENNUMMER_SAP, MESSMITTELGRUPPE,
                  DATUM_NAECHSTE_PRUEFUNG, PRUEFINTERVALL, EINHEIT_PRUEFINTERVALL,
                  FAELLIGKEIT_STOP
           FROM "dbo.MESSMITTEL"
           WHERE """ + _nonblank("KUNDENNUMMER_SAP")
    )
    for uuid, customer, group, due, interval, unit, stopped in cur:
        yield {
            "instrument": uuid,
            "customer": _digest(customer),
            "equipment_group": group if group is not None else "Unknown",
            "last_calibration": None,
            "recorded_due": due[:10] if due else None,
            "nominal_interval": interval,
            "interval_unit": unit,
            "stopped": 1 if stopped == 1 else (0 if stopped == 0 else None),
        }


def extract_instrument_events(conn: sqlite3.Connection):
    cur = conn.execute(
        """SELECT MESSMITTEL_UUID, KUNDENNUMMER_SAP, BEGINN,
                  COALESCE(MESSMITTELGRUPPE,'Unknown') AS equipment_group
           FROM "dbo.KALIBRIERUNGEN"
           WHERE BEGINN >= ? AND BEGINN < ?
             AND """ + _nonblank("KUNDENNUMMER_SAP") + """
             AND MESSMITTEL_UUID IS NOT NULL""",
        (HISTORY_START, HISTORY_END),
    )
    for uuid, customer, beginn, group in cur:
        stamp = beginn[:19]
        yield {
            "event": _digest(f"{uuid}|{stamp}"),
            "instrument": uuid,
            "customer": _digest(customer),
            "calibration_date": beginn[:10],
            "equipment_group": group,
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline SQLite extracts for the snapshot builder.")
    parser.add_argument("--source", required=True, help="Path to perschmann.sqlite")
    args = parser.parse_args()
    ROOT.mkdir(exist_ok=True)
    conn = sqlite3.connect(f"file:{args.source}?mode=ro", uri=True)
    try:
        _write_streamed(ROOT / "monthly_history.json", extract_monthly(conn))
        _write_streamed(ROOT / "industry.json", extract_industry(conn))
        _write_streamed(ROOT / "groups.json", extract_groups(conn))
        _write_streamed(ROOT / "instruments.json", extract_instruments(conn))
        _write_streamed(ROOT / "instrument_events.json", extract_instrument_events(conn))
    finally:
        conn.close()


if __name__ == "__main__":
    main()
