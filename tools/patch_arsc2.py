#!/usr/bin/env python3
# Patch callers of AssetManager.containsAllocatedTable()Z in a jar:
#   invoke-virtual {vX}, containsAllocatedTable ; move-result vY
# becomes
#   const/16 vY, 0 ; nop ; nop
# The method itself is left untouched (patching it breaks verification).
import sys, zipfile, struct, hashlib, zlib

def uleb(b, o):
    r = s = 0
    while True:
        x = b[o]; o += 1
        r |= (x & 0x7f) << s; s += 7
        if x < 0x80: return r, o

FMT = {}
for ops, ln in [((0x00,0x01,0x04,0x07,0x0a,0x0b,0x0c,0x0d,0x0e,0x0f,0x10,0x11,0x12,0x1d,0x1e,0x21,0x27,0x28)+tuple(range(0x7b,0x90))+tuple(range(0xb0,0xd0)),1),
                ((0x02,0x05,0x08,0x13,0x15,0x16,0x19,0x1a,0x1c,0x1f,0x20,0x22,0x23,0x29)+tuple(range(0x2d,0x3e))+tuple(range(0x44,0x6e))+tuple(range(0x90,0xb0))+tuple(range(0xd0,0xe3))+(0xfe,0xff),2),
                ((0x03,0x06,0x09,0x14,0x17,0x1b,0x24,0x25,0x26,0x2a,0x2b,0x2c)+tuple(range(0x6e,0x73))+tuple(range(0x74,0x79))+(0xfc,0xfd),3),
                ((0xfa,0xfb),4),((0x18,),5)]:
    for x in ops: FMT[x] = ln

def insn_len(d, p):
    op = d[p]
    if op == 0x00 and d[p + 1] != 0:
        ident = d[p + 1]
        if ident == 1: return 4 + struct.unpack_from('<H', d, p + 2)[0] * 2
        if ident == 2: return 2 + struct.unpack_from('<H', d, p + 2)[0] * 4
        if ident == 3:
            w = struct.unpack_from('<H', d, p + 2)[0]; n = struct.unpack_from('<I', d, p + 4)[0]
            return 4 + (n * w + 1) // 2
    return FMT[op]

def patch_dex(d):
    d = bytearray(d)
    u32 = lambda o: struct.unpack_from('<I', d, o)[0]
    str_off, type_off, proto_off = u32(60), u32(68), u32(76)
    meth_n, meth_off = u32(88), u32(92)
    cls_n, cls_off = u32(96), u32(100)
    def string(i):
        o = u32(str_off + 4 * i); _, o = uleb(d, o)
        return bytes(d[o:d.index(0, o)]).decode('utf-8', 'replace')
    tname = lambda t: string(u32(type_off + 4 * t))
    mids = set()
    for i in range(meth_n):
        cl, pr, nm = struct.unpack_from('<HHI', d, meth_off + 8 * i)
        if string(nm) == 'containsAllocatedTable' and tname(cl) == 'Landroid/content/res/AssetManager;':
            mids.add(i)
    if not mids: return None, 0
    hits = 0
    for c in range(cls_n):
        o = u32(cls_off + 32 * c + 24)
        if not o: continue
        sf, o = uleb(d, o); inf, o = uleb(d, o); dm, o = uleb(d, o); vm, o = uleb(d, o)
        for _ in range(sf + inf): _, o = uleb(d, o); _, o = uleb(d, o)
        for _ in range(dm + vm):
            _, o = uleb(d, o); _, o = uleb(d, o); code, o = uleb(d, o)
            if not code: continue
            n = u32(code + 12); p = code + 16; end = p + 2 * n
            while p < end:
                op = d[p]
                if op in (0x6e, 0x74) and struct.unpack_from('<H', d, p + 2)[0] in mids \
                        and p + 6 < end and d[p + 6] == 0x0a:          # move-result vY
                    y = d[p + 7]
                    d[p:p + 8] = bytes([0x13, y, 0, 0, 0, 0, 0, 0])     # const/16 vY,0 ; nop ; nop
                    hits += 1; p += 8; continue
                p += 2 * insn_len(d, p)
    if hits:
        d[12:32] = hashlib.sha1(d[32:]).digest()
        struct.pack_into('<I', d, 8, zlib.adler32(bytes(d[12:])) & 0xffffffff)
    return bytes(d), hits

total = 0
for src, dst in zip(sys.argv[1::2], sys.argv[2::2]):
    zin = zipfile.ZipFile(src); zout = zipfile.ZipFile(dst, 'w'); t = 0
    for info in zin.infolist():
        data = zin.read(info.filename)
        if info.filename.startswith('classes') and info.filename.endswith('.dex'):
            new, h = patch_dex(data)
            if h: print(f'{src.split("/")[-1]} {info.filename}: {h} call(s) -> false'); data = new; t += h
        zout.writestr(info, data, compress_type=info.compress_type)
    zout.close(); total += t
    if not t: print(src.split('/')[-1], ': no callers (unchanged copy written)')
print('TOTAL', total)
