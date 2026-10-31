"""Build the site's data: site/data.js and site/stack/<ID>/ (the cascade's layers, loaded on demand).

Usage: python3 -I build_data.py <pdf_contracts.json> <GLP clone> <site dir>
Reads files only.  AGORA's text and cascade come from the GLP clone's programs/agora and cascade/AGORA.
"""
import json, re, sys, os, shutil, subprocess

pdf_json, GLP, SITE = sys.argv[1:4]

OWNER = {'GKK': 'GSC', 'GSG': 'GSC', 'GC': 'Currencies', 'GSN': 'GSC', 'GnW': 'GAI',
         'GFF': 'GFF', 'GB': 'Currencies', 'LBM': 'LBM', 'CSSN': 'CSSN', 'GAI': 'GAI',
         'GSNP': 'GAI', 'AGORA': 'Nimrod'}
EXTENDS = {'GKK': [], 'GSG': ['GKK'], 'GC': ['GKK'], 'GSN': ['GSG'], 'GnW': ['GSG'],
           'GFF': ['GSG'], 'GB': ['GC'], 'LBM': ['GSG'], 'CSSN': ['GSN', 'GnW'],
           'GAI': ['GnW'], 'GSNP': ['GSN', 'GAI'], 'AGORA': ['GB']}
# one plain line, an icon and a family per contract (the site's own words)
ABOUT = {
    'GKK': ('🔑', 'identity', 'Who you are and who you know: a key of your own, meeting people, introducing them.'),
    'GSG': ('🤝', 'social', 'Friends: become friends by agreeing, and end a friendship.'),
    'GSN': ('💬', 'social', 'Messages and groups among friends.'),
    'GnW': ('🛡️', 'care', 'Wards: agents a person creates and looks after, who act only through their guardians.'),
    'GAI': ('🤖', 'care', 'AI agents with an accountable developer and an accountable owner.'),
    'GSNP': ('✍️', 'social', 'Forwarding with provenance: every forward adds a signature you can see.'),
    'CSSN': ('🧒', 'care', 'A social network safe for children: parents, kids-only groups, coming of age.'),
    'GC': ('🪙', 'money', 'Personal currencies: everyone can issue their own coins.'),
    'GB': ('📜', 'money', 'Bonds with maturity dates, and escrow, on top of coins.'),
    'GFF': ('📰', 'social', 'Feeds and followers, delivered from friend to friend.'),
    'LBM': ('🚗', 'mobility', 'Ride sharing: tell a friend where you are and agree on a ride.'),
    'AGORA': ('🧺', 'money', 'Barter: make things, post them on a market wall, trade them.'),
}
LAYERS = [('schemas', 'schemas.txt'), ('verdict', 'verdict.txt'), ('vmat', 'vmat.tex'),
          ('platform', 'platform.vglp'), ('glp', 'platform.glp')]


def split_top(s):
    out, depth, buf = [], 0, ''
    for ch in s:
        if ch in '([': depth += 1
        if ch in ')]': depth -= 1
        if ch == ',' and depth == 0: out.append(buf.strip()); buf = ''; continue
        buf += ch
    if buf.strip(): out.append(buf.strip())
    return out


def parse_schemas(path):
    if not os.path.exists(path): return [], []
    header, out, cur = [], [], None
    for line in open(path).read().split('\n'):
        if not line.strip(): continue
        if line.startswith('    at '):
            m = re.match(r'    at (.+?): (.*)$', line)
            r = {'role': m.group(1), 'need': [], 'not': [], 'add': [], 'del': []}
            for it in split_top(m.group(2)):
                if it.startswith('not '): r['not'].append(it[4:])
                elif it.startswith('+'): r['add'].append(it[1:])
                elif it.startswith('-'): r['del'].append(it[1:])
                else: r['need'].append(it)
            cur['roles'].append(r)
        elif re.match(r'^[a-z_0-9]+\(', line):
            m = re.match(r'^([a-z_0-9]+)\((.*?)\)(?: \| (.*?))? :$', line)
            roles, _, vars_ = m.group(2).partition(';')
            cur = {'name': m.group(1), 'head': line[:-2], 'constraint': m.group(3) or '',
                   'parties': split_top(roles), 'vars': [x.strip() for x in vars_.split(',') if x.strip()],
                   'roles': []}
            out.append(cur)
        else:
            header.append(line.strip())
    return header, out


def pragmas_of(path):
    if not os.path.exists(path): return []
    lines = open(path).read().split('\n')
    return [l for l in lines[lines.index('Pragmas') + 1:] if l.strip()] if 'Pragmas' in lines else []


glp_commit = subprocess.run(['git', '-C', GLP, 'log', '-1', '--format=%H %cs'],
                            capture_output=True, text=True).stdout.split()

contracts = json.load(open(pdf_json))
for c in contracts: c['source'] = 'pdf'
lines = [l for l in open(f'{GLP}/programs/agora/AGORA.txt').read().split('\n') if l and not l.startswith('%')]
cl = []
for l in lines[2:lines.index('Pragmas')]:
    m = re.match(r'(\d)\. (\S) (.+?)\.\s+(.*)$', l)
    cl.append({'n': int(m.group(1)), 'mod': m.group(2), 'name': m.group(3), 'text': m.group(4)})
contracts.append({'id': 'AGORA', 'title': 'Grassroots Barter', 'preamble': lines[1], 'clauses': cl,
                  'noteBefore': '', 'source': 'agora'})

shutil.rmtree(f'{SITE}/stack', ignore_errors=True)
live = {d[5:].upper() for d in os.listdir(f'{GLP}/programs/vglp/cva') if d.startswith('live_')}
for c in contracts:
    cid = c['id']
    c['owner'], c['extends'] = OWNER[cid], EXTENDS[cid]
    c['icon'], c['family'], c['about'] = ABOUT[cid]
    d = f'{GLP}/cascade/{cid}'
    c['cascade'] = os.path.isdir(d)
    c['schemaHeader'], c['schemas'] = parse_schemas(f'{d}/schemas.txt')
    c['verdict'] = open(f'{d}/verdict.txt').read().strip() if c['cascade'] else ''
    c['pragmas'] = pragmas_of(f'{d}/{cid}.txt')
    c['live'] = cid.upper() in live
    c['layers'] = {}
    for k, f in LAYERS:
        if os.path.exists(f'{d}/{f}'):
            os.makedirs(f'{SITE}/stack/{cid}', exist_ok=True)
            shutil.copy(f'{d}/{f}', f'{SITE}/stack/{cid}/{f}')
            c['layers'][k] = {'file': f'stack/{cid}/{f}', 'lines': sum(1 for _ in open(f'{d}/{f}'))}

byid = {c['id']: c for c in contracts}
def ancestors(cid):
    out = []
    for p in EXTENDS[cid]: out += [p] + ancestors(p)
    return out
for c in contracts:
    for s in c['schemas']:
        s['from'] = c['id']
        for a in ancestors(c['id']):
            if any(x['name'] == s['name'] for x in byid[a]['schemas']): s['from'] = a

data = {'contracts': contracts, 'glpCommit': glp_commit,
        'pdf': 'the contracts as Udi revised them on 2026-10-30 (Coordination #11)'}
open(f'{SITE}/data.js', 'w').write('window.DATA = ' + json.dumps(data, ensure_ascii=False) + ';\n')
for c in contracts:
    print(c['id'], len(c['schemas']), 'live' if c['live'] else '', list(c['layers']))
