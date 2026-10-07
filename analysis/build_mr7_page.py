"""Generate an offline HTML artifact with aggregate data, no credentials."""
import json
from pathlib import Path
root=Path(__file__).parent
data=json.loads((root/'mr7/planner_data.json').read_text())
embedded=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
html=(root/'mr7_planner_template.html').read_text().replace('__DATA__',embedded)
target=root.parent/'challenge1_mr7.html'
target.write_text(html)
print(target)
