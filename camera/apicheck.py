import os,re,sys,glob,zipfile,subprocess
apk,fw=sys.argv[1],sys.argv[2]; W=os.path.expanduser('~/m12x/all')
if not os.path.isdir(W):
    os.makedirs(W); z=zipfile.ZipFile(apk); bs=[f for f in glob.glob(os.path.expanduser('~/smali/baksmali*.jar'))][0]
    for n in z.namelist():
        if re.match(r'classes\d*\.dex$',n):
            open(W+'/'+n,'wb').write(z.read(n)); subprocess.run(['java','-jar',bs,'d',W+'/'+n,'-o',W+'/sm'],check=True)
own=set()
for r,_,fs in os.walk(W+'/sm'):
    for f in fs: own.add('L'+os.path.relpath(os.path.join(r,f),W+'/sm')[:-6]+';')
calls=set()
for r,_,fs in os.walk(W+'/sm'):
    for f in fs:
        for m in re.finditer(r'invoke-\S+ \{[^}]*\}, (L(?:android|com/samsung|com/sec)/[^;]+;)->(\w+)\(',open(os.path.join(r,f)).read()):
            if m.group(1) not in own: calls.add((m.group(1),m.group(2)))
blob=b''
for j in glob.glob(fw+'/framework/*.jar'):
    try:
        z=zipfile.ZipFile(j)
        for n in z.namelist():
            if n.endswith('.dex'): blob+=z.read(n)
    except Exception: pass
miss=sorted(c for c in calls if bytes([len(c[1])])+c[1].encode()+b'\0' not in blob)
print('framework calls:',len(calls),' missing:',len(miss))
for c,m in miss[:40]: print(' ',c,m)
