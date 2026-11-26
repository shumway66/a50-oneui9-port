#!/usr/bin/env python3
# Print const-string literals used inside methods of classes matching a prefix.
# usage: dexstrings.py file.jar 'Lcom/android/server/accessibility/AccessibilityManagerService'
import sys, zipfile, struct
def uleb(b,o):
    r=s=0
    while True:
        x=b[o];o+=1;r|=(x&0x7f)<<s;s+=7
        if x<0x80:return r,o
FMT={}
for ops,ln in [((0x00,0x01,0x04,0x07,0x0a,0x0b,0x0c,0x0d,0x0e,0x0f,0x10,0x11,0x12,0x1d,0x1e,0x21,0x27,0x28)+tuple(range(0x7b,0x90))+tuple(range(0xb0,0xd0)),1),
 ((0x02,0x05,0x08,0x13,0x15,0x16,0x19,0x1a,0x1c,0x1f,0x20,0x22,0x23,0x29)+tuple(range(0x2d,0x3e))+tuple(range(0x44,0x6e))+tuple(range(0x90,0xb0))+tuple(range(0xd0,0xe3))+(0xfe,0xff),2),
 ((0x03,0x06,0x09,0x14,0x17,0x1b,0x24,0x25,0x26,0x2a,0x2b,0x2c)+tuple(range(0x6e,0x73))+tuple(range(0x74,0x79))+(0xfc,0xfd),3),((0xfa,0xfb),4),((0x18,),5)]:
    for x in ops:FMT[x]=ln
def ilen(d,p):
    op=d[p]
    if op==0 and d[p+1]:
        i=d[p+1]
        if i==1:return 4+struct.unpack_from('<H',d,p+2)[0]*2
        if i==2:return 2+struct.unpack_from('<H',d,p+2)[0]*4
        if i==3:w=struct.unpack_from('<H',d,p+2)[0];n=struct.unpack_from('<I',d,p+4)[0];return 4+(n*w+1)//2
    return FMT.get(op,1)
jar,pref=sys.argv[1],sys.argv[2].encode()
z=zipfile.ZipFile(jar); out=set()
for nme in z.namelist():
    if not nme.endswith('.dex'):continue
    d=z.read(nme)
    if pref not in d:continue
    u=lambda o:struct.unpack_from('<I',d,o)[0]
    so,to,cn,co=u(60),u(68),u(96),u(100)
    def st(i):
        o=u(so+4*i);_,o=uleb(d,o);return d[o:d.index(0,o)].decode('utf-8','replace')
    for c in range(cn):
        b=co+32*c
        if not st(u(to+4*u(b))).encode().startswith(pref):continue
        o=u(b+24)
        if not o:continue
        sf,o=uleb(d,o);inf,o=uleb(d,o);dm,o=uleb(d,o);vm,o=uleb(d,o)
        for _ in range(sf+inf):_,o=uleb(d,o);_,o=uleb(d,o)
        for _ in range(dm+vm):
            _,o=uleb(d,o);_,o=uleb(d,o);code,o=uleb(d,o)
            if not code:continue
            n=u(code+12);p=code+16;e=p+2*n
            while p<e:
                op=d[p]
                if op==0x1a:out.add(st(struct.unpack_from('<H',d,p+2)[0]))
                elif op==0x1b:out.add(st(u(p+2)))
                p+=2*ilen(d,p)
for s in sorted(out):
    if '.' in s and s.upper()!=s.lower() and (s.isupper() or 'action' in s.lower() or 'intent' in s.lower()) or ('.' in s and s.split('.')[-1].isupper()):
        print(s)
