"""Read-only anonymous customer context; SQL password prompted, never saved."""
import getpass,json,re
from pathlib import Path
import pyodbc
ROOT=Path(__file__).parent/'customers'
ROOT.mkdir(exist_ok=True)
queries={
 'industry':"""SELECT CONVERT(varchar(64),HASHBYTES('SHA2_256',k.KUNDENNUMMER_SAP),2) AS customer,COALESCE(b.Branche,'Unknown') AS industry FROM (SELECT DISTINCT KUNDENNUMMER_SAP FROM dbo.KALIBRIERUNGEN WHERE NULLIF(LTRIM(RTRIM(KUNDENNUMMER_SAP)),'') IS NOT NULL) k LEFT JOIN (SELECT KundenNr,MIN(Branche) AS Branche FROM dbo.Kunde_Branche GROUP BY KundenNr) b ON k.KUNDENNUMMER_SAP=b.KundenNr""",
 'groups':"""SELECT CONVERT(varchar(64),HASHBYTES('SHA2_256',KUNDENNUMMER_SAP),2) AS customer,COALESCE(MESSMITTELGRUPPE,'Unknown') AS equipment_group,COUNT_BIG(*) AS calibrations FROM dbo.KALIBRIERUNGEN WHERE BEGINN>='2025-09-01' AND BEGINN<'2026-09-01' AND NULLIF(LTRIM(RTRIM(KUNDENNUMMER_SAP)),'') IS NOT NULL GROUP BY KUNDENNUMMER_SAP,MESSMITTELGRUPPE""",
 'industry_duplicates':"""SELECT COUNT_BIG(*) AS customers_with_conflicting_industry FROM (SELECT KundenNr FROM dbo.Kunde_Branche GROUP BY KundenNr HAVING COUNT(DISTINCT Branche)>1) s""",
 'monthly_history':"""SELECT CONVERT(varchar(64),HASHBYTES('SHA2_256',KUNDENNUMMER_SAP),2) AS customer,CONVERT(char(7),BEGINN,126) AS month,COUNT_BIG(*) AS calibrations,COUNT(DISTINCT MESSMITTEL_UUID) AS instruments,COUNT(DISTINCT MESSMITTELGRUPPE) AS equipment_groups,COUNT(DISTINCT MESSRAUM) AS labs FROM dbo.KALIBRIERUNGEN WHERE BEGINN>='20240101' AND BEGINN<'20260901' AND NULLIF(LTRIM(RTRIM(KUNDENNUMMER_SAP)),'') IS NOT NULL GROUP BY KUNDENNUMMER_SAP,CONVERT(char(7),BEGINN,126) ORDER BY customer,month""",
 'date_settings':"""SELECT @@LANGUAGE AS language,CONVERT(char(10),CAST('2025-09-01' AS datetime),126) AS interpreted_hyphenated_date"""
}
pw=getpass.getpass('SQL password (not saved): ')
conn=pyodbc.connect('DRIVER={ODBC Driver 18 for SQL Server};SERVER=tcp:192.168.1.200,1433;DATABASE=PeCalHackathon2026;UID=PeCalHackathonParticipant;PWD={'+pw.replace('}','}}')+'};Encrypt=yes;TrustServerCertificate=yes;',timeout=20,autocommit=True)
del pw
conn.timeout=120
for name,sql in queries.items():
 sql=re.sub(r"'(\d{4})-(\d{2})-(\d{2})'",r"'\1\2\3'",sql) if name!='date_settings' else sql
 c=conn.execute(sql); cols=[v[0] for v in c.description]; rows=[dict(zip(cols,row)) for row in c.fetchall()]
 (ROOT/f'{name}.json').write_text(json.dumps(rows,ensure_ascii=False)); print(name,len(rows),flush=True)
conn.close()
