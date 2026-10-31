import json, sys, os, re
sys.path.insert(0, os.path.dirname(__file__))
from menu_spec import spec
GLP, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
titles = {}
for c in json.load(open(sys.argv[3])) if len(sys.argv) > 3 else []:
    titles[c['id']] = c['title']
for d in sorted(os.listdir(f'{GLP}/programs/vglp/cva')):
    if not d.startswith('live_'): continue
    c = d[5:]
    s = spec(f'{GLP}/programs/vglp/cva/{d}/platform.vglp')
    s['id'] = c.upper() if c != 'gnw' else 'GnW'
    s['title'] = titles.get(s['id'], s['id'])
    s['calendar'] = 'cal(alice, N)' in open(f'{GLP}/programs/vglp/cva/{d}/self.glp').read()
    s.pop('raw_items')
    json.dump(s, open(f'{OUT}/{c}.json', 'w'))
    print(c, len(s['proposals']))
