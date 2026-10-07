"""Build self-contained HTML from real model outputs; no external assets."""
import json,re
from pathlib import Path
ROOT=Path(__file__).parent
base=(ROOT/'mr7_planner_template.html').read_text()
style=base.split('<style>')[1].split('</style>')[0]
chart=base[base.index('function chart('):base.index('function driverHtml(')]
data=json.loads((ROOT/'customers/dashboard_data.json').read_text())
page=(ROOT/'customer_dashboard_template.html').read_text().replace('__STYLE__',style).replace('__CHART__',chart).replace('__DATA__',json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c'))
out=ROOT.parent/'challenge2_customers.html';out.write_text(page);print(out)
