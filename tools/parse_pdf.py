import re, json, sys
lines = open(sys.argv[1]).read().split('\n')
# start after the figure caption
start = next(i for i,l in enumerate(lines) if l.strip().startswith('Formally,'))
lines = lines[start:]
MOD = {'GKK':'○■■','GSG':'◆■','GSN':'■■■■','GnW':'■■■■■','GAI':'○■','GSNP':'◆',
       'CSSN':'◆■○◆','GC':'■■■■■○','GB':'■○■■■','GFF':'■■■■','LBM':'■■■'}
contracts=[]; notes=[]; cur=None; mode=None
head=re.compile(r'^\s*(GKK|GSG|GSN|GnW|GAI|GSNP|CSSN|GC|GB|GFF|LBM): (.+)$')
clause=re.compile(r'^\s*(\d)\.\s+(.*)$')
for raw in lines:
    s=raw.strip()
    if not s or re.fullmatch(r'\d', s): continue
    m=head.match(raw)
    if m:
        cur={'id':m.group(1),'title':m.group(2).strip(),'preamble':'','clauses':[],'noteBefore':' '.join(notes)}
        notes=[]; contracts.append(cur); mode='pre'; continue
    m=clause.match(raw)
    if m and cur and mode in('pre','cl'):
        cur['clauses'].append({'n':int(m.group(1)),'text':m.group(2).strip()}); mode='cl'; continue
    # note lines: unindented-ish text outside boxes
    if s.startswith('Note that') or s.startswith('An instrument') or s.startswith('Formally'):
        notes.append(s); mode='note'; continue
    if mode=='note': notes.append(s); continue
    if mode=='pre': cur['preamble']=(cur['preamble']+' '+s).strip()
    elif mode=='cl': cur['clauses'][-1]['text']+=' '+s
for c in contracts:
    mods=MOD[c['id']]; assert len(mods)==len(c['clauses']),(c['id'],len(c['clauses']))
    for cl,md in zip(c['clauses'],mods):
        cl['mod']=md
        t=cl['text'].replace('’',"'").replace('- ship','ship'); t=re.sub(r'\s+',' ',t)
        mm=re.match(r'([^.]+)\.\s+(.*)',t); cl['name']=mm.group(1); cl['text']=mm.group(2)
    c['noteBefore']=c['noteBefore'].replace('’',"'"); c['preamble']=c['preamble'].replace('member- ship','membership')
json.dump(contracts,open(sys.argv[2],'w'),ensure_ascii=False,indent=1)
for c in contracts:
    print(c['id'],'|',c['title'],'|',c['preamble']); print('  note:',c['noteBefore'][:90])
    for cl in c['clauses']: print('  ',cl['n'],cl['mod'],cl['name'],'::',cl['text'][:70])
