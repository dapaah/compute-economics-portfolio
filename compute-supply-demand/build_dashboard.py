"""Build a self-contained local HTML artifact from registries and tested JS."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def build():
    text=(HERE/'dashboard.template.html').read_text(encoding='utf-8')
    for token,filename in [('__SUPPLY_JSON__','parameters.json'),('__DEMAND_JSON__','demand_parameters.json')]:
        blob=json.loads((HERE/filename).read_text(encoding='utf-8'))
        text=text.replace(token,json.dumps(blob,ensure_ascii=False).replace('<','\\u003c'))
    text=text.replace('__MODEL_JS__',(HERE/'model.js').read_text(encoding='utf-8'))
    return text


if __name__=='__main__':
    (HERE/'deliverable_capacity.html').write_text(build(),encoding='utf-8')
