"""Read-only SQL export. Credentials are prompted and never written to disk."""
import getpass
import argparse
import re
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
import pyodbc

ROOT = Path(__file__).parent / 'mr7'
ROOT.mkdir(exist_ok=True)
QUERIES = {
'weekly_calibrations': """
SELECT MESSRAUM AS lab, DATEADD(day,-(DATEDIFF(day,'19000101',CAST(BEGINN AS date))%7),CAST(BEGINN AS date)) AS week,
 COUNT_BIG(*) AS calibrations,COUNT(DISTINCT MESSMITTEL_UUID) AS instruments
FROM dbo.KALIBRIERUNGEN WHERE BEGINN>='2024-01-01'
GROUP BY MESSRAUM,DATEADD(day,-(DATEDIFF(day,'19000101',CAST(BEGINN AS date))%7),CAST(BEGINN AS date)) ORDER BY lab,week""",
'monthly_calibrations': """
SELECT MESSRAUM AS lab,CONVERT(char(7),BEGINN,126) AS month,COUNT_BIG(*) AS calibrations
FROM dbo.KALIBRIERUNGEN WHERE BEGINN>='2024-01-01' GROUP BY MESSRAUM,CONVERT(char(7),BEGINN,126) ORDER BY lab,month""",
'actual_capacity': """
SELECT Kalendertag AS day,MESSRAUM AS lab,KST AS cost_center,[IST Anwesend STD] AS attendance_hours,
[IST Krank STD] AS sick_hours,[IST Urlaub STD] AS vacation_hours,[IST Sonstiges STD] AS other_hours,
[IST-Stunden Gesamtergebnis  STD] AS total_hours FROM dbo.[Ist_Stunden_24-26] ORDER BY lab,day""",
'planned_capacity': """
SELECT [Kalendertag (Intervall)] AS day,MESSRAUM AS lab,KST AS cost_center,[SOLL Anwesend STD] AS attendance_hours,
[SOLL Krank STD] AS sick_hours,[SOLL Urlaub STD] AS vacation_hours,[SOLL Sonstiges STD] AS other_hours,
[Gesamtergebnis STD] AS total_hours FROM dbo.[Soll-Kapa] ORDER BY lab,day""",
'service_key_sample': """
SELECT TOP(5) AUFTRAGSNUMMER AS order_number,MESSMITTEL_UUID AS instrument FROM dbo.KALIBRIERUNGEN WHERE MESSRAUM='MR7'
UNION ALL SELECT TOP(5) AUFTRAGSNUMMER_SAP,UUID_KALIBRIERGEGENSTAND FROM dbo.DIENSTLEISTUNGEN""",
'instruments': """
SELECT CONVERT(varchar(64),HASHBYTES('SHA2_256',MESSMITTEL_UUID),2) AS instrument,
CONVERT(varchar(64),HASHBYTES('SHA2_256',KUNDENNUMMER_SAP),2) AS customer,
MESSMITTELGRUPPE AS equipment_group,MESSMITTELTYP AS equipment_type,DATUM_LETZTE_PRUEFUNG AS last_calibration,
DATUM_NAECHSTE_PRUEFUNG AS due_date,PRUEFINTERVALL AS declared_interval,EINHEIT_PRUEFINTERVALL AS interval_unit,
FAELLIGKEIT_TYP AS due_type,FAELLIGKEIT_STOP AS due_stopped,LETZTE_BEWERTUNG AS assessment
FROM dbo.MESSMITTEL WHERE MESSRAUM='MR7'""",
'calibration_events': """
SELECT CONVERT(varchar(64),HASHBYTES('SHA2_256',MESSMITTEL_UUID),2) AS instrument,
CAST(BEGINN AS date) AS day,MESSMITTELGRUPPE AS equipment_group,MESSMITTELTYP AS equipment_type
FROM dbo.KALIBRIERUNGEN WHERE MESSRAUM='MR7' AND BEGINN>='2024-01-01' ORDER BY MESSMITTEL_UUID,BEGINN""",
'weekly_workload': """
WITH calmap AS (
 SELECT MESSMITTEL_UUID,AUFTRAGSNUMMER,MIN(MESSRAUM) AS lab
 FROM dbo.KALIBRIERUNGEN GROUP BY MESSMITTEL_UUID,AUFTRAGSNUMMER HAVING COUNT(DISTINCT MESSRAUM)=1),
times AS (SELECT Artikelnummer,MAX(BearbeitungszeitMin) AS minutes FROM dbo.ArtikelnummerZeit GROUP BY Artikelnummer)
SELECT c.lab,DATEADD(day,-(DATEDIFF(day,'19000101',CAST(d.QUITTIERT_AM AS date))%7),CAST(d.QUITTIERT_AM AS date)) AS week,
COUNT_BIG(*) AS services,SUM(CASE WHEN t.minutes>0 THEN 1 ELSE 0 END) AS matched_services,
SUM(COALESCE(t.minutes,0))/60 AS standard_hours
FROM dbo.DIENSTLEISTUNGEN d JOIN calmap c ON d.UUID_KALIBRIERGEGENSTAND=c.MESSMITTEL_UUID AND d.AUFTRAGSNUMMER_SAP=c.AUFTRAGSNUMMER
LEFT JOIN times t ON d.KATALOGNUMMER=t.Artikelnummer
WHERE d.QUITTIERT_AM>='2024-01-01' AND c.lab LIKE 'MR%'
GROUP BY c.lab,DATEADD(day,-(DATEDIFF(day,'19000101',CAST(d.QUITTIERT_AM AS date))%7),CAST(d.QUITTIERT_AM AS date)) ORDER BY c.lab,week""",
'workload_drivers': """
WITH calmap AS (
 SELECT MESSMITTEL_UUID,AUFTRAGSNUMMER,MIN(MESSRAUM) AS lab
 FROM dbo.KALIBRIERUNGEN GROUP BY MESSMITTEL_UUID,AUFTRAGSNUMMER HAVING COUNT(DISTINCT MESSRAUM)=1),
times AS (SELECT Artikelnummer,MAX(BearbeitungszeitMin) AS minutes,MAX(Beschreibung) AS description FROM dbo.ArtikelnummerZeit GROUP BY Artikelnummer)
SELECT COALESCE(t.description,d.DIENSTLEISTUNGSTYP) AS description,d.DIENSTLEISTUNGSTYP AS service_type,
COUNT_BIG(*) AS services,COUNT(t.minutes) AS matched_services,SUM(COALESCE(t.minutes,0))/60 AS standard_hours
FROM dbo.DIENSTLEISTUNGEN d JOIN calmap c ON d.UUID_KALIBRIERGEGENSTAND=c.MESSMITTEL_UUID AND d.AUFTRAGSNUMMER_SAP=c.AUFTRAGSNUMMER
LEFT JOIN times t ON d.KATALOGNUMMER=t.Artikelnummer
WHERE c.lab='MR7' AND d.QUITTIERT_AM>='2025-09-01' AND d.QUITTIERT_AM<'2026-09-01'
GROUP BY COALESCE(t.description,d.DIENSTLEISTUNGSTYP),d.DIENSTLEISTUNGSTYP ORDER BY standard_hours DESC""",
'source_metadata': """
SELECT 'calibrations' AS dataset,MAX(BEGINN) AS last_date FROM dbo.KALIBRIERUNGEN
UNION ALL SELECT 'services',MAX(QUITTIERT_AM) FROM dbo.DIENSTLEISTUNGEN
UNION ALL SELECT 'actual_capacity',MAX(Kalendertag) FROM dbo.[Ist_Stunden_24-26]
UNION ALL SELECT 'planned_capacity',MAX([Kalendertag (Intervall)]) FROM dbo.[Soll-Kapa]""",
}

def convert(v):
    if isinstance(v,Decimal):
        return float(v)
    if hasattr(v,'isoformat'):
        return v.isoformat()
    return v

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--only',nargs='+',choices=QUERIES);args=parser.parse_args()
    password=getpass.getpass('SQL password (not saved): ')
    escaped=password.replace('}','}}')
    connection=pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER=tcp:192.168.1.200,1433;DATABASE=PeCalHackathon2026;UID=PeCalHackathonParticipant;PWD={'+escaped+'};Encrypt=yes;TrustServerCertificate=yes;',timeout=20,autocommit=True)
    del password,escaped
    connection.timeout=180
    statuses={}
    for name,sql in QUERIES.items():
        if args.only and name not in args.only: continue
        sql=re.sub(r"'(\d{4})-(\d{2})-(\d{2})'",r"'\1\2\3'",sql)
        print('Exporting',name,flush=True)
        try:
            cursor=connection.execute(sql)
            columns=[d[0] for d in cursor.description]
            rows=[{k:convert(v) for k,v in zip(columns,row)} for row in cursor.fetchall()]
            (ROOT/f'{name}.json').write_text(json.dumps(rows,ensure_ascii=False,separators=(',',':')))
            statuses[name]={'rows':len(rows),'ok':True}
            print(name,len(rows),'rows',flush=True)
        except Exception as exc:
            statuses[name]={'ok':False,'error':str(exc)}
            print(name,'failed:',type(exc).__name__,flush=True)
    connection.close()
    metadata_path=ROOT/'export_metadata.json';old=json.loads(metadata_path.read_text()) if metadata_path.exists() and args.only else {};old.setdefault('statuses',{}).update(statuses)
    metadata_path.write_text(json.dumps({'exported_at':datetime.now(timezone.utc).isoformat(),'statuses':old['statuses'],'queries':{n:re.sub(r"'(\d{4})-(\d{2})-(\d{2})'",r"'\1\2\3'",s) for n,s in QUERIES.items()}},indent=2))
