"""Read an offline SQL export into the existing normalized snapshot inputs.

Source and outputs are private local files. No writes are made to SQLite.
The complete-month cutoff is explicit, rather than inferred from export time.
"""

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, default=Path("analysis/customers"))
    parser.add_argument("--history-start", default="2024-01")
    parser.add_argument("--complete-through", default="2026-08")
    args = parser.parse_args()
    year, month = map(int, args.complete_through.split("-"))
    stop = f"{year + (month == 12):04d}-{month % 12 + 1:02d}-01"
    year_start = f"{year - (month < 12):04d}-{month % 12 + 1:02d}-01"
    start = args.history_start + "-01"
    queries = {
        "industry": ('SELECT sha(k.KUNDENNUMMER_SAP) AS customer, COALESCE(b.Branche,\'Unknown\') AS industry FROM (SELECT DISTINCT KUNDENNUMMER_SAP FROM "dbo.KALIBRIERUNGEN" WHERE trim(COALESCE(KUNDENNUMMER_SAP,\'\'))<>\'\') k LEFT JOIN (SELECT KundenNr,MIN(Branche) AS Branche FROM "dbo.Kunde_Branche" GROUP BY KundenNr) b ON k.KUNDENNUMMER_SAP=b.KundenNr', ()),
        "groups": ('SELECT sha(KUNDENNUMMER_SAP) AS customer,COALESCE(MESSMITTELGRUPPE,\'Unknown\') AS equipment_group,COUNT(*) AS calibrations FROM "dbo.KALIBRIERUNGEN" WHERE BEGINN>=? AND BEGINN<? AND trim(COALESCE(KUNDENNUMMER_SAP,\'\'))<>\'\' GROUP BY KUNDENNUMMER_SAP,MESSMITTELGRUPPE', (year_start, stop)),
        "monthly_history": ('SELECT sha(KUNDENNUMMER_SAP) AS customer,substr(BEGINN,1,7) AS month,COUNT(*) AS calibrations,COUNT(DISTINCT MESSMITTEL_UUID) AS instruments,COUNT(DISTINCT MESSMITTELGRUPPE) AS equipment_groups,COUNT(DISTINCT MESSRAUM) AS labs FROM "dbo.KALIBRIERUNGEN" WHERE BEGINN>=? AND BEGINN<? AND trim(COALESCE(KUNDENNUMMER_SAP,\'\'))<>\'\' GROUP BY KUNDENNUMMER_SAP,substr(BEGINN,1,7) ORDER BY customer,month', (start, stop)),
        "instruments": ('SELECT MESSMITTEL_UUID AS instrument,sha(KUNDENNUMMER_SAP) AS customer,COALESCE(MESSMITTELGRUPPE,\'Unknown\') AS equipment_group,NULL AS last_calibration,substr(DATUM_NAECHSTE_PRUEFUNG,1,10) AS recorded_due,PRUEFINTERVALL AS nominal_interval,EINHEIT_PRUEFINTERVALL AS interval_unit,CASE WHEN FAELLIGKEIT_STOP=1 THEN 1 WHEN FAELLIGKEIT_STOP=0 THEN 0 ELSE NULL END AS stopped FROM "dbo.MESSMITTEL" WHERE trim(COALESCE(KUNDENNUMMER_SAP,\'\'))<>\'\'', ()),
        "instrument_events": ('SELECT sha(MESSMITTEL_UUID||\'|\'||substr(BEGINN,1,19)) AS event,MESSMITTEL_UUID AS instrument,sha(KUNDENNUMMER_SAP) AS customer,substr(BEGINN,1,10) AS calibration_date,COALESCE(MESSMITTELGRUPPE,\'Unknown\') AS equipment_group FROM "dbo.KALIBRIERUNGEN" WHERE BEGINN>=? AND BEGINN<? AND trim(COALESCE(KUNDENNUMMER_SAP,\'\'))<>\'\' AND MESSMITTEL_UUID IS NOT NULL', (start, stop)),
    }
    args.output.mkdir(parents=True, exist_ok=True)
    if any((args.output / f"{name}.json").exists() for name in queries):
        raise FileExistsError("Choose a fresh output folder to preserve prior extracts")
    with sqlite3.connect(args.source.resolve().as_uri() + "?mode=ro", uri=True) as db:
        db.create_function("sha", 1, lambda value: hashlib.sha256(str(value).encode()).hexdigest().upper())
        db.execute("PRAGMA query_only=ON")
        counts = {}
        for name, (query, parameters) in queries.items():
            cursor = db.execute(query, parameters)
            columns = [item[0] for item in cursor.description]
            target = args.output / f"{name}.json"
            temp = target.with_suffix(".json.tmp")
            count = 0
            with temp.open("x", encoding="utf-8") as output:
                output.write("[")
                for row in cursor:
                    if count:
                        output.write(",")
                    output.write(json.dumps(dict(zip(columns, row)), ensure_ascii=False))
                    count += 1
                output.write("]")
            temp.replace(target)
            counts[name] = count
            print(name, count, flush=True)
        (args.output / "offline_export_metadata.json").write_text(
            json.dumps({"source": str(args.source), "complete_through_month": args.complete_through,
                        "history_start": args.history_start, "row_counts": counts}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
