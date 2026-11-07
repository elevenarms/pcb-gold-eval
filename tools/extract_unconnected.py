import json,glob,re,sys
out=[]
for f in sorted(glob.glob(sys.argv[1]+'/**/*.jsonl',recursive=True)):
  sid=f.split('/')[-1][:8]
  for line in open(f):
    try:r=json.loads(line)
    except:continue
    m=r.get('message',{})
    c=m.get('content') if isinstance(m,dict) else None
    if not isinstance(c,list):continue
    for b in c:
      if b.get('type')=='tool_result':
        t=b.get('content')
        if isinstance(t,list): t=' '.join(x.get('text','') for x in t if isinstance(x,dict))
        t=str(t)
        for mm in re.finditer(r'(?:^|\s)(\d+) \[unconnected_items\]|Found (\d+) unconnected items|unconnected_items[\'"]?\)?:? (\d+)|(\d+) unconnected',t):
          n=next(g for g in mm.groups() if g)
          out.append((r.get('timestamp','')[:19],sid,int(n)))
for o in sorted(set(out)): print(*o)
