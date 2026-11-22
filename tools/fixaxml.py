import sys, struct, zlib, os, shutil
apk, OLD, NEW = sys.argv[1], sys.argv[2], sys.argv[3]
d = bytearray(open(apk,'rb').read())
eocd = d.rfind(b'PK\x05\x06'); cd_size, cd_off = struct.unpack_from('<II', d, eocd+12)
ents=[]; p=cd_off
while p < cd_off+cd_size:
    fl,meth,_,_,crc,cs,us,nl,el,cl = struct.unpack_from('<HHHHIIIHHH', d, p+8)
    ents.append(dict(cdp=p, name=bytes(d[p+46:p+46+nl]), lho=struct.unpack_from('<I',d,p+42)[0], meth=meth, fl=fl, cs=cs, us=us)); p += 46+nl+el+cl
def read_pool(b, sp):
    t,hs,sz,cnt,scnt,flg,ss,sts = struct.unpack_from('<HHIIIIII', b, sp)
    utf8 = bool(flg & 0x100); offs=[struct.unpack_from('<I',b,sp+hs+4*i)[0] for i in range(cnt)]; out=[]
    for o in offs:
        o += sp+ss
        if utf8:
            n=b[o]; o+= 2 if n&0x80 else 1
            n=b[o]
            if n&0x80: n=((n&0x7f)<<8)|b[o+1]; o+=2
            else: o+=1
            out.append(bytes(b[o:o+n]).decode('utf-8'))
        else:
            n=struct.unpack_from('<H',b,o)[0]; o+=2
            if n&0x8000: n=((n&0x7fff)<<16)|struct.unpack_from('<H',b,o)[0]; o+=2
            out.append(bytes(b[o:o+2*n]).decode('utf-16le'))
    styles = bytes(b[sp+sts: sp+sz]) if scnt else b''
    styleoffs = bytes(b[sp+hs+4*cnt: sp+hs+4*cnt+4*scnt])
    return dict(hs=hs, sz=sz, flg=flg, utf8=utf8, strs=out, scnt=scnt, styles=styles, styleoffs=styleoffs)
def build_pool(P):
    data=b''; offs=[]
    for s in P['strs']:
        offs.append(len(data))
        if P['utf8']:
            e=s.encode()
            L=lambda n: bytes([n]) if n<0x80 else bytes([0x80|(n>>8), n&0xff])
            assert len(s)<0x8000 and len(e)<0x8000
            data+=L(len(s))+L(len(e))+e+b'\0'
        else:
            u=s.encode('utf-16le'); assert len(s)<0x8000
            data+=struct.pack('<H',len(s))+u+b'\0\0'
    data+=b'\0'*((-len(data))%4)
    cnt=len(P['strs']); hs=28; ss=hs+4*cnt+4*P['scnt']
    sts = ss+len(data) if P['scnt'] else 0
    body = b''.join(struct.pack('<I',o) for o in offs) + P['styleoffs'] + data + P['styles']
    return struct.pack('<HHIIIIII',1,hs,hs+len(body),cnt,P['scnt'],P['flg'],ss,sts) + body
changed=0
for e in sorted(ents, key=lambda x: x['lho']):
    if not (e['name'].startswith(b'res/') and e['name'].endswith(b'.xml')): continue
    lh=e['lho']; nl,el=struct.unpack_from('<HH',d,lh+26); ds=lh+30+nl+el; raw=bytes(d[ds:ds+e['cs']])
    x = raw if e['meth']==0 else zlib.decompress(raw,-15)
    if x[:2]!=b'\x03\x00' or OLD.encode('utf-16le') not in x and OLD.encode() not in x: continue
    P=read_pool(x,8)
    if OLD not in P['strs']: continue
    P['strs']=[NEW if s==OLD else s for s in P['strs']]
    newpool=build_pool(P); oldsz=P['sz']
    nx=bytearray(x[:8]+newpool+x[8+oldsz:]); struct.pack_into('<I',nx,4,len(nx))
    nraw = bytes(nx) if e['meth']==0 else (lambda c: c.compress(bytes(nx))+c.flush())(zlib.compressobj(9,zlib.DEFLATED,-15))
    assert e['meth']==0 or zlib.decompress(nraw,-15)==bytes(nx)
    crc=zlib.crc32(nx)&0xffffffff; dl=0
    if e['fl']&8:
        q=ds+len(raw); dl=16 if d[q:q+4]==b'PK\x07\x08' else 12
        struct.pack_into('<H',d,lh+6,e['fl']&~8); struct.pack_into('<H',d,e['cdp']+8,e['fl']&~8)
    delta=len(nraw)-len(raw)-dl
    struct.pack_into('<III',d,lh+14,crc,len(nraw),len(nx)); struct.pack_into('<III',d,e['cdp']+16,crc,len(nraw),len(nx))
    d[ds:ds+len(raw)+dl]=nraw
    for f in ents:
        if f['lho']>lh: f['lho']+=delta; f['cdp']+=delta; struct.pack_into('<I',d,f['cdp']+42,f['lho'])
        elif f['cdp']>lh: f['cdp']+=delta
    e['cdp']+= delta if e['cdp']>lh else 0
    cd_off+=delta; eocd+=delta; struct.pack_into('<I',d,eocd+16,cd_off)
    print('patched', e['name'].decode(), f'{OLD} -> {NEW}'); changed+=1
if not changed: sys.exit('string not found in any res/*.xml - nothing changed')
n=1
while os.path.exists(os.path.expanduser(f'~/framework-res.apk.bak_axml{n}')): n+=1
shutil.copy2(apk, os.path.expanduser(f'~/framework-res.apk.bak_axml{n}')); open(apk,'wb').write(d)
print('backup ~/framework-res.apk.bak_axml%d'%n)
