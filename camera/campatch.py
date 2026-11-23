import os,re,glob,zipfile,subprocess
H=os.path.expanduser('~/m12x'); os.chdir(H)
bs=glob.glob(os.path.expanduser('~/smali/baksmali*.jar'))[0]; sm=[j for j in glob.glob(os.path.expanduser('~/smali/smali*.jar')) if 'baksmali' not in j][0]
z=zipfile.ZipFile('SamsungCamera/SamsungCamera.apk'); new={}
for n in sorted(x for x in z.namelist() if re.match(r'classes\d*\.dex$',x)):
    d=z.read(n)
    if n!='classes2.dex' and b'semSetDisablePreviewScreenshots' not in d and b'etCurrentUser' not in d: continue
    out='sm' if n=='classes2.dex' else 'p_'+n
    if n!='classes2.dex':
        subprocess.run(['rm','-rf',out]); open('t.dex','wb').write(d); subprocess.run(['java','-jar',bs,'d','t.dex','-o',out],check=True)
    c1=c2=0
    for r,_,fs in os.walk(out):
        for f in fs:
            p=os.path.join(r,f); s=open(p).read()
            s,a=re.subn(r'invoke-\S+ \{[^}]*\}, L[^;]+;->semSetDisablePreviewScreenshots\(Z\)V','nop',s)
            s,b=re.subn(r'invoke-\S+ \{[^}]*\}, L(?:android|com/samsung/android/(?!camera))[^;]*;->(?:sem)?[gG]etCurrentUser\w*\(\)I(\s*\n\s*)move-result (\w+)',r'nop\1const/16 \2, 0x0',s)
            if a or b: open(p,'w').write(s); c1+=a; c2+=b
    subprocess.run(['java','-jar',sm,'a',out,'--api','34','-o','o_'+n],check=True); new[n]=open('o_'+n,'rb').read()
    print(n,'screenshot calls:',c1,' getCurrentUser calls:',c2)
zo=zipfile.ZipFile('SamsungCamera.patched.apk','w')
for i in z.infolist():
    d=new.get(i.filename) or z.read(i.filename)
    m=zipfile.ZipInfo(i.filename,i.date_time); m.compress_type=i.compress_type; m.external_attr=i.external_attr
    if m.compress_type==zipfile.ZIP_STORED:
        a=4096 if i.filename.endswith('.so') else 4; off=zo.fp.tell()+30+len(m.filename.encode()); m.extra=b'\0'*((a-off%a)%a)
    zo.writestr(m,d)
zo.close(); print('apk rebuilt')
