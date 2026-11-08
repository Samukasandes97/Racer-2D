"""Rodar DEPOIS de converter_mapa.py/mascara_estrada.py/heightfield_sombra.py.
1) Tampa buracos do chao (rio, terrenos vazios, faixa em volta do mapa) com grama e deixa o chao dirigivel (grid camada 0).
2) Cria muretas nas bordas de viadutos/rodovias elevadas (geometria estatica) e (a fisica usa a regra de queda: degrau > .09 = parede).
Gera tiles extras f_X_Z.wav (mesmo formato dos tiles) e os acrescenta em tiles.json."""
import json,os,struct,sys,numpy as np
from PIL import Image
from scipy import ndimage as ndi
M=sys.argv[1] if len(sys.argv)>1 else '../../demos/mundo-aberto/mapa'
c=json.load(open(M+'/tiles.json'));GW,GH,L,CELL,x0,z0,T=c['GW'],c['GH'],c['LAY'],c['CELL'],c['x0'],c['z0'],c['T']
c['tiles']=[t for t in c['tiles'] if not t['f'].startswith('f_')]
g=np.fromfile(M+'/grid.wav',dtype=np.int16).reshape(L,GH,GW).copy()
tp=np.fromfile(M+'/top.wav',dtype=np.uint8)[:GW*GH].reshape(GH,GW)
road=np.unpackbits(np.fromfile(M+'/road.wav',dtype=np.uint8))[:GW*GH].reshape(GH,GW)==1
top=-.2+tp/255*2.4
# ---- atlas: texel de grama e de concreto no slot 63 (junto dos texels do telhado)
at=Image.open(M+'/atlas.png').convert('RGB');rx,ry=(63%8)*256,(63//8)*256
rng=np.random.RandomState(7)
gr=np.clip(np.array([74,118,58])+rng.randint(-6,7,(16,16,1)),0,255).astype(np.uint8);at.paste(Image.fromarray(gr),(rx+80,ry+120))
cc=np.clip(np.array([150,148,142])+rng.randint(-5,6,(16,16,1)),0,255).astype(np.uint8);at.paste(Image.fromarray(cc),(rx+80,ry+80))
at.save(M+'/atlas.png',optimize=True)
UG=((rx+88)/2048,(ry+128)/2048);UC=((rx+88)/2048,(ry+88)/2048)
# ---- 1) buracos
lowe=(g[0]==-32768)&(top<.06)
env=ndi.binary_dilation((g[0]!=-32768)|(top>=.06),iterations=45)
hole=lowe&env
g[0][hole]=3
print('celulas de buraco preenchidas',hole.sum())
g.tofile(M+'/grid.wav')
quads=[]   # (x0,z0,x1,z1,y)
h=hole.copy();used=np.zeros_like(h)
for j in range(GH):
    i=0
    while i<GW:
        if h[j,i] and not used[j,i]:
            k=i
            while k<GW and h[j,k] and not used[j,k]:k+=1
            j2=j+1
            while j2<GH and h[j2,i:k].all() and not used[j2,i:k].any():j2+=1
            used[j:j2,i:k]=True;quads.append((i,j,k,j2));i=k
        else:i+=1
print('quads',len(quads))
# ---- 2) bordas de viaduto
Z=-32768
def best(dy,dx,lim):
    out=np.full((GH,GW),-9.,np.float32)
    for k in range(L):
        a=np.full((GH,GW),Z,np.int16)
        ys=slice(max(0,-dy),GH-max(0,dy));yd=slice(max(0,dy),GH-max(0,-dy));xs=slice(max(0,-dx),GW-max(0,dx));xd=slice(max(0,dx),GW-max(0,-dx))
        a[ys,xs]=g[k][yd,xd]
        v=np.where(a==Z,-9,a/1000.).astype(np.float32);ok=(v<=lim)&(a!=Z);out=np.where(ok&(v>out),v,out)
    return out
walls=[]   # (side,j,i,h)  side 0:-x 1:+x 2:-z 3:+z
for k in range(L):
    hk=np.where(g[k]==Z,-9,g[k]/1000.).astype(np.float32);cell=(g[k]!=Z)&(hk>.06)&road
    for side,(dy,dx) in enumerate([(0,-1),(0,1),(-1,0),(1,0)]):
        nb=best(dy,dx,hk+.035);e=cell&(hk>.1)&(nb>-9)&(nb<hk-.07)
        for j,i in zip(*np.nonzero(e)):walls.append((side,j,i,hk[j,i]))
print('bordas',len(walls))
ws={}
for sd,j,i,h_ in walls:ws[(sd,j,i)]=h_
runs=[];seen=set()
for (sd,j,i),h_ in sorted(ws.items()):
    if (sd,j,i) in seen:continue
    dj,di=(1,0) if sd<2 else (0,1);n=1;seen.add((sd,j,i));hh=h_
    while (sd,j+dj*n,i+di*n) in ws and (sd,j+dj*n,i+di*n) not in seen and abs(ws[(sd,j+dj*n,i+di*n)]-hh)<.006:
        seen.add((sd,j+dj*n,i+di*n));n+=1
    if n>=5:runs.append((sd,j,i,n,hh))
print('segmentos',len(runs))
WH,WT=.05,.012
def rect(a,b,y):return [(a[0],y,a[1]),(b[0],y,a[1]),(b[0],y,b[1]),(a[0],y,b[1])]
tris={}  # tile -> (pos list, uv list)
def add(tx,tz,quad,uv):
    P,U=tris.setdefault((tx,tz),([],[]));n=len(P)
    P.extend(quad);U.extend([uv]*4);P.append(None)  # marcador de quad
for (i0,j0,i1,j1) in quads:
    xa,za,xb,zb=x0+i0*CELL,z0+j0*CELL,x0+i1*CELL,z0+j1*CELL
    # fatia por tile para nao cruzar limites
    tx0,tx1=int((xa-x0)//T),int((xb-x0-1e-6)//T);tz0,tz1=int((za-z0)//T),int((zb-z0-1e-6)//T)
    for tx in range(tx0,tx1+1):
        for tz in range(tz0,tz1+1):
            a=max(xa,x0+tx*T),max(za,z0+tz*T);b=min(xb,x0+(tx+1)*T),min(zb,z0+(tz+1)*T)
            add(tx,tz,rect(a,b,.003),UG)
for s,j,i,nn,h_ in runs:
    xa,za=x0+i*CELL,z0+j*CELL;xb,zb=xa+CELL*(nn if s>=2 else 1),za+CELL*(nn if s<2 else 1)
    if s==0:a,b=(xa,za),(xa+WT,zb)
    elif s==1:a,b=(xb-WT,za),(xb,zb)
    elif s==2:a,b=(xa,za),(xb,za+WT)
    else:a,b=(xa,zb-WT),(xb,zb)
    tx,tz=int((xa-x0)//T),int((za-z0)//T);y=h_+WH
    add(tx,tz,rect(a,b,y),UC)
    # faces laterais (4) como quads verticais
    def vq(p,q):add(tx,tz,[(p[0],h_,p[1]),(q[0],h_,q[1]),(q[0],y,q[1]),(p[0],y,p[1])],UC)
    vq((a[0],a[1]),(b[0],a[1]));vq((b[0],b[1]),(a[0],b[1]));vq((a[0],b[1]),(a[0],a[1]));vq((b[0],a[1]),(b[0],b[1]))
n=0
for (tx,tz),(P,U) in sorted(tris.items()):
    pos=[];uv=[];ind=[];q=[];
    for p,u in zip(P,U+[None]*0 if False else U):pass
    verts=[];uvs=[];cur=[];curu=[]
    k=0;idx=0
    pts=[p for p in P if p is not None];us=U
    pos=np.array(pts,np.float64);uvv=np.array(us,np.float64)
    nq=len(pos)//4;ind=np.array([[4*m,4*m+1,4*m+2,4*m,4*m+2,4*m+3] for m in range(nq)],np.uint32).reshape(-1)
    parts=[(0,len(pos))]
    # divide em lotes < 65000 vertices
    for s in range(0,nq,16000):
        ss=slice(s*4,min(nq,s+16000)*4);ps=pos[ss];us_=uvv[ss];nv=len(ps)
        mn=ps.min(0);mx=ps.max(0);ext=np.maximum(mx-mn,1e-6)
        qq=np.round((ps-mn)/ext*65535).astype(np.uint16);qu=np.round(us_*65535).astype(np.uint16)
        qs=np.full(nv,255,np.uint8);ii=np.array([[4*m,4*m+1,4*m+2,4*m,4*m+2,4*m+3,4*m+2,4*m+1,4*m,4*m+3,4*m+2,4*m] for m in range(nv//4)],np.uint16).reshape(-1)   # dupla face
        name='f_%d_%d_%d.wav'%(tx,tz,s//16000)
        with open(M+'/'+name,'wb') as f:
            f.write(struct.pack('<II',nv,len(ii)));f.write(qq.tobytes());f.write(qu.tobytes());f.write(qs.tobytes());f.write(b'\0'*((4-nv%4)%4));f.write(ii.tobytes())
        c['tiles'].append(dict(f=name,tx=tx,tz=tz,mn=mn.round(5).tolist(),ext=ext.round(5).tolist(),nv=nv,ni=len(ii)));n+=1
json.dump(c,open(M+'/tiles.json','w'))
print('tiles extras',n)
