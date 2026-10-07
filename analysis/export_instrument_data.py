"""Read-only instrument-level extract for the Member 1 snapshot builder.

Run after export_customer_data.py. SQL password prompted, never saved.
Column evidence: analysis/challenge_data_{audit,validation,followup}.{sql,txt}.
Writes analysis/customers/instruments.json + instrument_events.json
(gitignored, like the other extracts).
"""
import getpass,json
from pathlib import Path
import pyodbc
ROOT=Path(__file__).parent/'customers'
ROOT.mkdir(exist_ok=True)
queries={
 'instruments':"""SELECT m.MESSMITTEL_UUID AS instrument,CONVERT(varchar(64),HASHBYTES('SHA2_256',m.KUNDENNUMMER_SAP),2) AS customer,COALESCE(m.MESSMITTELGRUPPE,'Unknown') AS equipment_group,CONVERT(char(10),MAX(k.BEGINN),126) AS last_calibration,CONVERT(char(10),m.DATUM_NAECHSTE_PRUEFUNG,126) AS recorded_due,m.PRUEFINTERVALL AS nominal_interval,m.EINHEIT_PRUEFINTERVALL AS interval_unit,CASE WHEN m.FAELLIGKEIT_STOP=1 THEN 1 WHEN m.FAELLIGKEIT_STOP=0 THEN 0 ELSE NULL END AS stopped FROM dbo.MESSMITTEL m LEFT JOIN dbo.KALIBRIERUNGEN k ON k.MESSMITTEL_UUID=m.MESSMITTEL_UUID WHERE NULLIF(LTRIM(RTRIM(m.KUNDENNUMMER_SAP)),'') IS NOT NULL GROUP BY m.MESSMITTEL_UUID,m.KUNDENNUMMER_SAP,m.MESSMITTELGRUPPE,m.DATUM_NAECHSTE_PRUEFUNG,m.PRUEFINTERVALL,m.EINHEIT_PRUEFINTERVALL,m.FAELLIGKEIT_STOP""",
 'instrument_events':"""SELECT CONVERT(varchar(64),HASHBYTES('SHA2_256',CONCAT(k.MESSMITTEL_UUID,'|',CONVERT(varchar(19),k.BEGINN,126))),2) AS event,k.MESSMITTEL_UUID AS instrument,CONVERT(varchar(64),HASHBYTES('SHA2_256',k.KUNDENNUMMER_SAP),2) AS customer,CONVERT(char(10),k.BEGINN,126) AS calibration_date,COALESCE(k.MESSMITTELGRUPPE,'Unknown') AS equipment_group FROM dbo.KALIBRIERUNGEN k WHERE k.BEGINN>='20240101' AND k.BEGINN<'20260901' AND NULLIF(LTRIM(RTRIM(k.KUNDENNUMMER_SAP)),'') IS NOT NULL AND k.MESSMITTEL_UUID IS NOT NULL ORDER BY instrument,calibration_date""",
}
pw=getpass.getpass('SQL password (not saved): ')
conn=pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER=tcp:192.168.1.200,1433;DATABASE=PeCalHackathon2026;UID=PeCalHackathonParticipant;PWD={'+pw.replace('}','}}')+'};Encrypt=yes;TrustServerCertificate=yes;',timeout=20,autocommit=True)
del pw
conn.timeout=600
for name,sql in queries.items():
 c=conn.execute(sql); cols=[v[0] for v in c.description]; rows=[dict(zip(cols,row)) for row in c.fetchall()]
 (ROOT/f'{name}.json').write_text(json.dumps(rows,ensure_ascii=False)); print(name,len(rows),flush=True)
conn.close()
