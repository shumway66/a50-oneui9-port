#!/usr/bin/env python3
# Make boolean methods return true in a jar's dex files.
# usage: dexret.py file.jar ClassSubstring method1,method2   (only methods returning Z are patched)
import sys, struct, zlib, hashlib, os, shutil
jar, CLS, METHODS = sys.argv[1], sys.argv[2], sys.argv[3].split(',')
DRY = '--dry' in sys.argv
def uleb(b, o):
    r=s=0
    while True:
        x=b[o]; o+=1; r|=(x&0x7f)<<s; s+=7
        if x<0x80: return r,o
def patch_dex(dx):
    dx=bytearray(dx)
    def u32(o): return struct.unpack_from('<I',dx,o)[0]
    sids_n,sids_o=u32(56),u32(60); tids_n,tids_o=u32(64),u32(68); pids_o=u32(76); mids_n,mids_o=u32(88),u32(92); cd_n,cd_o=u32(96),u32(100)
    def string(i):
        o=u32(sids_o+4*i); n,o=uleb(dx,o); e=dx.index(0,o); return bytes(dx[o:e]).decode('utf-8','replace')
    def tname(i): return string(u32(tids_o+4*i))
    hits=[]
    for c in range(cd_n):
        b=cd_o+32*c; cidx,_,_,_,_,_,cdata,_=struct.unpack_from('<8I',dx,b)
        cn=tname(cidx)
        if CLS not in cn or not cdata: continue
        o=cdata; sf,o=uleb(dx,o); inf,o=uleb(dx,o); dm,o=uleb(dx,o); vm,o=uleb(dx,o)
        for _ in range(sf+inf): _,o=uleb(dx,o); _,o=uleb(dx,o)
        midx=0
        for k in range(dm+vm):
            if k==dm: midx=0
            d,o=uleb(dx,o); midx+=d; _,o=uleb(dx,o); code,o=uleb(dx,o)
            cls_i,proto_i,name_i=struct.unpack_from('<HHI',dx,mids_o+8*midx)
            mn=string(name_i); rt=tname(u32(pids_o+12*proto_i+4))
            if mn in METHODS and rt=='Z' and code:
                regs,ins,outs,tries,dbg,isz=struct.unpack_from('<HHHHII',dx,code)
                if regs<1 or isz<2: print('  skip (too small)',cn,mn); continue
                ip=code+16; old=bytes(dx[ip:ip+4])
                if old==bytes.fromhex('12100f00'): print('  already',cn,mn); continue
                print(f'  found {cn}->{mn} regs={regs} ins={ins} insns={isz} first={old.hex()}')
                dx[ip:ip+4]=bytes.fromhex('12100f00')   # const/4 v0, 1 ; return v0
                hits.append(f'{cn}->{mn}')
    if hits:
        dx[12:32]=hashlib.sha1(dx[32:]).digest(); struct.pack_into('<I',dx,8,zlib.adler32(bytes(dx[12:]))&0xffffffff)
    return bytes(dx),hits
d=bytearray(open(jar,'rb').read())
eocd=d.rfind(b'PK\x05\x06'); cd_size,cd_off=struct.unpack_from('<II',d,eocd+12)
ents=[]; p=cd_off
while p<cd_off+cd_size:
    fl,meth,_,_,crc,cs,us,nl,el,cl=struct.unpack_from('<HHHHIIIHHH',d,p+8)
    ents.append(dict(cdp=p,name=bytes(d[p+46:p+46+nl]),lho=struct.unpack_from('<I',d,p+42)[0],meth=meth,fl=fl,cs=cs)); p+=46+nl+el+cl
allhits=[]
for e in sorted(ents,key=lambda x:x['lho']):
    if not (e['name'].startswith(b'classes') and e['name'].endswith(b'.dex')): continue
    lh=e['lho']; nl,el=struct.unpack_from('<HH',d,lh+26); ds=lh+30+nl+el; raw=bytes(d[ds:ds+e['cs']])
    x=raw if e['meth']==0 else zlib.decompress(raw,-15)
    nx,hits=patch_dex(x)
    if not hits: continue
    allhits+=[e['name'].decode()+': '+h for h in hits]
    nraw=nx if e['meth']==0 else (lambda c:c.compress(nx)+c.flush())(zlib.compressobj(9,zlib.DEFLATED,-15))
    crc=zlib.crc32(nx)&0xffffffff; dl=0
    if e['fl']&8:
        q=ds+len(raw); dl=16 if d[q:q+4]==b'PK\x07\x08' else 12
        struct.pack_into('<H',d,lh+6,e['fl']&~8); struct.pack_into('<H',d,e['cdp']+8,e['fl']&~8)
    delta=len(nraw)-len(raw)-dl
    struct.pack_into('<III',d,lh+14,crc,len(nraw),len(nx)); struct.pack_into('<III',d,e['cdp']+16,crc,len(nraw),len(nx))
    d[ds:ds+len(raw)+dl]=nraw
    for f in ents:
        if f['lho']>lh: f['lho']+=delta
        f['cdp']+=delta                      # central directory lies after all file data
        struct.pack_into('<I',d,f['cdp']+42,f['lho'])
    cd_off+=delta; eocd+=delta; struct.pack_into('<I',d,eocd+16,cd_off)
if not allhits: sys.exit('no matching methods - nothing changed')
if DRY: sys.exit('dry run - nothing written')
bk=os.path.expanduser('~/cmp/'+os.path.basename(jar)+'.before_dexret')
if not os.path.exists(bk): shutil.copy2(jar,bk)
open(jar,'wb').write(d)
for h in allhits: print('PATCHED',h)
print('backup',bk)
