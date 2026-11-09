"""Rodar DEPOIS de preencher_buracos.py. As paginas de textura 128 e 158 nao vieram no zip do mapa (79 faces de chao ficavam cinza).
Cada face dessas copia a cor do chao vizinho (grama ou concreto, usando os texels criados em preencher_buracos.py)."""
import sys,json,struct,re,numpy as np
from PIL import Image
OBJ=sys.argv[1];M=sys.argv[2] if len(sys.argv)>2 else '../../demos/mundo-aberto/mapa'
order={}
for l in open(OBJ,errors='ignore'):
    if l.startswith('usemtl'):order.setdefault(l.split()[1],len(order))
bad=[order[n] for n in('page_128','page_158') if n in order];print('slots cinza',bad)
c=json.load(open(M+'/tiles.json'));at=np.array(Image.open(M+'/atlas.png').convert('RGB')).astype(float)
UG=(1880/2048,1920/2048);UC=(1880/2048,1880/2048)
def slotof(u,v):return int(v*2048//256)*8+int(u*2048//256)
fixed=0
for t in c['tiles']:
    if t['f'].startswith('f_'):continue
    fn=M+'/'+t['f'];b=bytearray(open(fn,'rb').read());nv,ni=struct.unpack_from('<II',b,0)
    pos=np.frombuffer(b,np.uint16,3*nv,8).reshape(nv,3).astype(float);uvo=8+6*nv
    uv=np.frombuffer(b,np.uint16,2*nv,uvo).reshape(nv,2).copy()
    uvf=uv/65535.
    sl=np.array([slotof(a,v) for a,v in uvf]);gray=np.isin(sl,bad)
    if not gray.any():continue
    mn=np.array(t['mn']);ext=np.array(t['ext']);P=mn+pos/65535*ext
    good=~gray&(P[:,1]<.05)
    if not good.any():col=UG
    for i in np.nonzero(gray)[0]:
        if good.any():
            d=np.hypot(P[good,0]-P[i,0],P[good,2]-P[i,2]);j=np.nonzero(good)[0][d.argmin()]
            px=at[min(2047,int(uvf[j,1]*2048)),min(2047,int(uvf[j,0]*2048))]
            col=UG if px[1]>px[0]+6 and px[1]>px[2]+6 else UC
        uv[i]=np.round(np.array(col)*65535)
    b[uvo:uvo+4*nv]=uv.astype(np.uint16).tobytes();open(fn,'wb').write(b);fixed+=int(gray.sum())
print('vertices corrigidos',fixed)

# ---- 2a etapa: faces de CHAO que usam os texels azul-acinzentado do 'telhado' (slot 63 x120..176,y120..136) viram concreto
rx,ry=1792,1792;n2=0
for t in c['tiles']:
    if t['f'].startswith('f_'):continue
    fn=M+'/'+t['f'];b=bytearray(open(fn,'rb').read());nv,ni=struct.unpack_from('<II',b,0)
    pos=np.frombuffer(b,np.uint16,3*nv,8).reshape(nv,3).astype(float);uvo=8+6*nv
    uv=np.frombuffer(b,np.uint16,2*nv,uvo).reshape(nv,2).copy();uvf=uv/65535.
    px=uvf[:,0]*2048;py=uvf[:,1]*2048
    roof=(px>=rx+118)&(px<rx+178)&(py>=ry+118)&(py<ry+138)
    if not roof.any():continue
    mn=np.array(t['mn']);ext=np.array(t['ext']);P=mn+pos/65535*ext
    low=roof&(P[:,1]<.08)
    if low.any():
        uv[low]=np.round(np.array(UC)*65535);b[uvo:uvo+4*nv]=uv.astype(np.uint16).tobytes();open(fn,'wb').write(b);n2+=int(low.sum())
print('vertices de chao com cor de telhado -> concreto',n2)
