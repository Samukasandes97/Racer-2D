"""Converte o mapa Chicago (OBJ gigante) em blocos leves para o navegador.
Uso: python3 converter_mapa.py <arquivo chicago_day_split.obj> <pasta textures PNG> <saida>
Gera: atlas.png (2048), tiles.json, t_X_Z_K.wav (posicao uint16, uv uint16, brilho uint8, indices uint16; extensao .wav so por compatibilidade de publicacao), grid.wav (4 camadas de altura/colisao)."""
import sys,json,os,re,struct,numpy as np
from PIL import Image,ImageDraw
OBJ,TEX,OUT=sys.argv[1:4]; os.makedirs(OUT,exist_ok=True)
T=12.8                       # tamanho do bloco (unidades do mapa)
CELL=0.2                     # celula da grade de colisao
# ---- le OBJ
V=[];VT=[];FV=[];FT=[];FM=[];mats={};cur=0
for l in open(OBJ,errors='ignore'):
    c=l[:2]
    if c=='v ':
        p=l.split();V.append((float(p[1]),float(p[2]),float(p[3])))
    elif c=='vt':
        p=l.split();VT.append((float(p[1]),float(p[2])))
    elif c=='f ':
        q=[t.split('/') for t in l.split()[1:]]
        for a,b,cc in ((0,1,2),(0,2,3)) if len(q)==4 else ((0,1,2),):
            FV.append([int(q[a][0]),int(q[b][0]),int(q[cc][0])]);FT.append([int(q[a][1]),int(q[b][1]),int(q[cc][1])]);FM.append(cur)
    elif l.startswith('usemtl'):
        n=l.split()[1];cur=mats.setdefault(n,len(mats))
V=np.array(V,np.float64);VT=np.array(VT,np.float64);FV=np.array(FV)-1;FT=np.array(FT)-1;FM=np.array(FM)
print('tris',len(FV),'mats',len(mats))
# ---- atlas 8x8 de paginas 256x256
slot={};atlas=Image.new('RGB',(2048,2048),(128,128,128));k=0
for n,i in sorted(mats.items(),key=lambda x:x[1]):
    pg=int(re.findall(r'\d+',n)[0]);f=os.path.join(TEX,'PAGE_%d.png'%pg)
    slot[i]=k
    if os.path.exists(f):atlas.paste(Image.open(f).convert('RGB'),((k%8)*256,(k//8)*256))
    k+=1
ROOFSLOT=63 if k<=63 else k-1
rx,ry=(ROOFSLOT%8)*256,(ROOFSLOT//8)*256
rng=np.random.RandomState(1)
blk=np.clip(np.array([58,60,70])+rng.randint(-5,6,(16,16,1)),0,255).astype(np.uint8)
atlas.paste(Image.fromarray(np.repeat(np.repeat(blk,1,0),1,1)),(rx+120,ry+120))
atlas.save(os.path.join(OUT,'atlas.png'),optimize=True)
print('mats',k,'slot telhado',ROOFSLOT)
# ---- vertices por canto (pos+uv atlas), brilho por normal
P=V[FV]                                   # (n,3,3)
nrm=np.cross(P[:,1]-P[:,0],P[:,2]-P[:,0]);ln=np.linalg.norm(nrm,axis=1);ok=ln>1e-12
nrm[ok]/=ln[ok,None]
sl=np.array([slot[m] for m in FM])
uv=VT[FT];u=np.clip(uv[...,0],0,1);v=np.clip(uv[...,1],0,1)
au=(sl[:,None]%8+u)/8;av=(sl[:,None]//8+(1-v))/8
ny=nrm[:,1]
shade=np.where(ny>.5,1.0,np.where(ny<-.5,.55,np.where(np.abs(nrm[:,0])>np.abs(nrm[:,2]),.74,.86)))
# ---- grade de colisao: altura do chao (mais baixa superficie virada pra cima), void = sem superficie
x0,x1=V[:,0].min(),V[:,0].max();z0,z1=V[:,2].min(),V[:,2].max()
GW=int((x1-x0)/CELL)+2;GH=int((z1-z0)/CELL)+2
def raster(idx,order):
    im=Image.new('F',(GW,GH),9e9 if order<0 else -9e9);d=ImageDraw.Draw(im)
    ys=P[idx,:,1].mean(1);o=np.argsort(ys)[::order]   # order=-1: desenha do mais alto ao mais baixo => o mais baixo fica por cima
    for t in idx[o]:
        d.polygon([((p[0]-x0)/CELL,(p[2]-z0)/CELL) for p in P[t]],fill=float(P[t,:,1].mean()))
    return np.array(im)
up=np.where((ny>.5))[0]
NB=0.08;LAY=4
hy=P[up,:,1].mean(1);band=np.floor((hy+0.5)/NB).astype(int)
layers=np.full((LAY,GH,GW),-32768,np.int16);cnt=np.zeros((GH,GW),np.int8);last=np.full((GH,GW),-9.0)
low=np.full((GH,GW),-9.0)
for bd in np.unique(band):
    r=raster(up[band==bd],1);valid=r>-8e8
    r[~valid]=-9
    if bd==np.unique(band)[0]:low=np.where(valid,r,low)
    new_=valid&((last<-8)|(r-last>0.12))&(cnt<LAY)
    for li in range(LAY):
        m=new_&(cnt==li);layers[li][m]=np.round(r[m]*1000).astype(np.int16)
    cnt=np.where(new_,cnt+1,cnt);last=np.where(new_,r,last)
print('camadas por celula',[int((cnt==i).sum()) for i in range(LAY+1)])
layers.tofile(os.path.join(OUT,'grid.wav'))
# ---- telhados: celulas sem superficie virada pra cima (topo dos predios) ganham um teto na altura da parede mais proxima
from scipy.ndimage import distance_transform_edt
void=(cnt==0)
vtop=np.full((GH,GW),-9.0)
side=np.where(np.abs(ny)<=.5)[0]
ix=np.clip(((P[side,:,0]-x0)/CELL).astype(int),0,GW-1).ravel();iz=np.clip(((P[side,:,2]-z0)/CELL).astype(int),0,GH-1).ravel();yy=P[side,:,1].ravel()
np.maximum.at(vtop,(iz,ix),yy)
src=(vtop>-8)&(~void)|((vtop>-8)&void)   # paredes dentro ou na borda
d,(ii,jj)=distance_transform_edt(~(vtop>-8),return_indices=True)
roofY=vtop[ii,jj]
ground=np.where(cnt>0,layers[0]/1000.0,-9)
roofvoid=void&(d<12)
roofY=np.where(roofvoid,np.maximum(roofY,0.05),-9)
# quads por corrida horizontal de mesma altura (quantizada)
rq=np.round(roofY/0.04)*0.04
RT=[]
for r_ in range(GH):
    row=rq[r_];c_=0
    while c_<GW:
        if not roofvoid[r_,c_]:c_+=1;continue
        e=c_
        while e+1<GW and e-c_<15 and roofvoid[r_,e+1] and row[e+1]==row[c_]:e+=1
        RT.append((c_,e+1,r_,row[c_]));c_=e+1
print('quads de telhado',len(RT))
rt=np.array(RT,np.float64)
xa=x0+rt[:,0]*CELL;xb=x0+rt[:,1]*CELL;za=z0+rt[:,2]*CELL;zb=za+CELL;yr=rt[:,3]+0.003
n_r=len(rt)
R0=np.stack([np.stack([xa,yr,za],1),np.stack([xb,yr,za],1),np.stack([xb,yr,zb],1)],1)
R1=np.stack([np.stack([xa,yr,za],1),np.stack([xb,yr,zb],1),np.stack([xa,yr,zb],1)],1)
# chao geral escuro sob o mapa inteiro (tampa buracos), em quadrados de 4 unidades
GQ=4.0;gq=[]
for gx in np.arange(x0,x1,GQ):
    for gz in np.arange(z0,z1,GQ):
        ex=min(gx+GQ,x1);ez=min(gz+GQ,z1)
        A=(gx,-0.17,gz);B=(ex,-0.17,gz);C=(ex,-0.17,ez);D=(gx,-0.17,ez)
        gq.append([A,B,C]);gq.append([A,C,D])
gq=np.array(gq,np.float64)
EXTRA=np.concatenate([R0,R1,gq])
ru=(ROOFSLOT%8*256+128)/2048;rv=(ROOFSLOT//8*256+128)/2048
P=np.concatenate([P,EXTRA]);n0=len(au)
au=np.concatenate([au,np.full((len(EXTRA),3),ru)]);av=np.concatenate([av,np.full((len(EXTRA),3),rv)])
shade=np.concatenate([shade,np.full(len(EXTRA),1.0)]);ok=np.concatenate([ok,np.ones(len(EXTRA),bool)])
# ---- blocos
cx=np.clip(((P[:,:,0].mean(1)-x0)//T).astype(int),0,None);cz=np.clip(((P[:,:,2].mean(1)-z0)//T).astype(int),0,None)
tiles=[];tot=0
for tx in range(cx.max()+1):
  for tz in range(cz.max()+1):
    sel=np.where((cx==tx)&(cz==tz)&ok)[0]
    if not len(sel):continue
    # parte em lotes de <= 20000 triangulos (< 65536 vertices)
    for part,s in enumerate(range(0,len(sel),20000)):
        ss=sel[s:s+20000]
        pos=P[ss].reshape(-1,3);uu=np.stack([au[ss].reshape(-1),av[ss].reshape(-1)],1);sh=np.repeat(shade[ss],3)
        key=np.concatenate([np.round(pos*2000).astype(np.int64),np.round(uu*20000).astype(np.int64),np.round(sh*100).astype(np.int64)[:,None]],1)
        _,first,inv=np.unique(key,axis=0,return_index=True,return_inverse=True)
        pos=pos[first];uu=uu[first];sh=sh[first];ind=inv.reshape(-1).astype(np.uint16)
        mn=pos.min(0);mx=pos.max(0);ext=np.maximum(mx-mn,1e-6)
        q=np.round((pos-mn)/ext*65535).astype(np.uint16)
        qu=np.round(np.clip(uu,0,1)*65535).astype(np.uint16)
        qs=np.round(sh*255).astype(np.uint8)
        nv=len(q);name='t_%d_%d_%d.wav'%(tx,tz,part)
        with open(os.path.join(OUT,name),'wb') as f:
            f.write(struct.pack('<II',nv,len(ind)));f.write(q.tobytes());f.write(qu.tobytes());f.write(qs.tobytes());f.write(b'\0'*((4-nv%4)%4));f.write(ind.tobytes())
        tiles.append(dict(f=name,tx=tx,tz=tz,mn=mn.round(5).tolist(),ext=ext.round(5).tolist(),nv=nv,ni=len(ind)));tot+=os.path.getsize(os.path.join(OUT,name))
json.dump(dict(x0=x0,z0=z0,T=T,CELL=CELL,GW=GW,GH=GH,LAY=LAY,tiles=tiles),open(os.path.join(OUT,'tiles.json'),'w'))
print('tiles',len(tiles),'bytes',tot,'grid',GW,GH)
