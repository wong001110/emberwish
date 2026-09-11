"""Generate original deterministic PNG/ICO assets using only Python's standard library."""
from pathlib import Path
import math, struct, zlib
ROOT = Path(__file__).resolve().parents[1]
def png(size):
    rows = bytearray()
    for y in range(size):
        rows.append(0)
        for x in range(size):
            u, v = (x + .5)/size, (y + .5)/size
            r, g, b, a = 32, 54, 49, 255
            if math.hypot(u-.5,v-.5)>.48: a=0
            if .23<u<.77 and .57<v<.72 and ((u-.5)/.3)**2+((v-.57)/.2)**2<1: r,g,b=224,178,124
            if abs(u-.5)<.023 and .27<v<.58: r,g,b=234,190,131
            if math.hypot(u-.5,v-.265)<.042: r,g,b=255,132,83
            rows.extend((r,g,b,a))
    def chunk(t, d): return struct.pack('!I',len(d))+t+d+struct.pack('!I',zlib.crc32(t+d)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',size,size,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(bytes(rows)))+chunk(b'IEND',b'')
out=ROOT/'src-tauri/icons'; out.mkdir(parents=True,exist_ok=True)
p=png(256); (out/'icon.png').write_bytes(p)
(out/'icon.ico').write_bytes(struct.pack('<HHH',0,1,1)+struct.pack('<BBBBHHII',0,0,0,0,1,32,len(p),22)+p)
print('Generated deterministic original icons.')
