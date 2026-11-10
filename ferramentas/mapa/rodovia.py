"""Rodar DEPOIS de preencher_buracos.py + corrigir_texturas.py. Acrescenta ao fim do mapa (z crescente) uma RODOVIA nova:
pista dupla com canteiro, curvas, trecho com TUNEL, POSTO de gasolina, postes, arvores, placa. Estende grid/obs/road/top e cria tiles r_*.wav,
mais nos/arestas de vias.json para o transito. Idempotente: guarda GH0/OH0 originais em tiles.json."""
import json,struct,sys,math,numpy as np
from PIL import Image
M=sys.argv[1] if len(sys.argv)>1 else '../../demos/mundo-aberto/mapa'
c=json.load(open(M+'/tiles.json'));GW,L,CELL,x0,z0,T,OS,OW=c['GW'],c['LAY'],c['CELL'],c['x0'],c['z0'],c['T'],c['OS'],c['OW']
GH0=c.setdefault('GH0',c['GH']);OH0=c.setdefault('OH0',c['OH'])
LEN=150.0;N=int(round(LEN/CELL));NO=int(round(LEN/OS));GH=GH0+N;OH=OH0+NO;zs=z0+GH0*CELL
c['tiles']=[t for t in c['tiles'] if not t['f'].startswith('r_')]
# ---- dados originais (truncados em GH0) ----
import os
raw=open(M+'/grid.wav','rb').read()+(open(M+'/grid2.wav','rb').read() if os.path.exists(M+'/grid2.wav') else b'')
g=np.frombuffer(raw,np.int16);g=g.reshape(L,-1,GW)[:,:GH0]
tp=np.fromfile(M+'/top.wav',np.uint8)[:GW*GH0].reshape(GH0,GW)
rd=np.unpackbits(np.fromfile(M+'/road.wav',np.uint8))[:GW*GH0].reshape(GH0,GW)
ob=np.unpackbits(np.fromfile(M+'/obs.wav',np.uint8))[:OW*OH0].reshape(OH0,OW)
G=np.full((L,GH,GW),-32768,np.int16);G[:,:GH0]=g
TP=np.full((GH,GW),21,np.uint8);TP[:GH0]=tp
RD=np.zeros((GH,GW),np.uint8);RD[:GH0]=rd
OB=np.zeros((OH,OW),np.uint8);OB[:OH0]=ob
# ---- texels no atlas (slot 63, linha y=160..) ----
at=Image.open(M+'/atlas.png').convert('RGB');rx,ry=1792,1792
COL={'asf':(62,65,72),'bra':(235,235,230),'ama':(240,190,40),'conc':(168,166,160),'concE':(110,110,116),'rail':(190,196,205),'grama':(74,118,58),
 'tronco':(92,64,40),'folha':(52,130,62),'folha2':(78,150,70),'lojaP':(236,236,228),'telhaV':(214,48,52),'bomba':(220,52,48),'vidro':(120,170,200),
 'placa':(24,110,70),'lamp':(255,238,170),'teto':(70,72,80),'poste':(120,124,132),'azul':(40,90,170)}
UV={}
for k,(n,col) in enumerate(COL.items()):
    ox,oy=(k%8)*20+4,160+(k//8)*20+4;at.paste(Image.new('RGB',(16,16),col),(rx+ox,ry+oy));UV[n]=((rx+ox+8)/2048,(ry+oy+8)/2048)
at.save(M+'/atlas.png',optimize=True)
# ---- eixo da rodovia ----
BASE=x0+525*CELL
def S(u,a,b):t=min(1,max(0,(u-a)/(b-a)));return t*t*(3-2*t)
def xc(z):u=z-zs;return BASE+6*S(u,6,36)-8*S(u,128,148)
def Hh(z):u=z-zs;return .30*S(u,4,24)-.30*S(u,26,42)        # colinas
def EV(z):u=z-zs;return .32*S(u,92,104)-.32*S(u,120,132)      # viaduto (rampa+tabuleiro)
def HR(z):return Hh(z)+EV(z)
def tang(z):e=.05;return math.atan2(xc(z+e)-xc(z-e),2*e)
RH,GR=.012,.003                      # altura da pista e do chao
MED,CAR,SHO,RAIL=.05,.38,.46,.50
quads={}   # tile -> list of (4 pts, uvname, shade)
def addq(p,tex,sh=255):
    ck=int((sum(q[0] for q in p)/4-x0)//T),int((sum(q[2] for q in p)/4-z0)//T);quads.setdefault(ck,[]).append((p,tex,sh))
def strip(za,zb,oa,ob_,y,tex,sh=255,rel=True):
    p=[]
    for z,o in ((za,oa),(za,ob_),(zb,ob_),(zb,oa)):p.append((xc(z)+o,y+(HR(z) if rel else 0),z))
    addq(p,tex,sh)
def wall(za,zb,o,y0,y1,tex,sh=255):
    addq([(xc(za)+o,y0+HR(za),za),(xc(zb)+o,y0+HR(zb),zb),(xc(zb)+o,y1+HR(zb),zb),(xc(za)+o,y1+HR(za),za)],tex,sh)
def box(cx,cz,w,d,y0,y1,tex,sh=255,roof=None):
    a,b,cc,dd=cx-w/2,cz-d/2,cx+w/2,cz+d/2
    addq([(a,y1,b),(cc,y1,b),(cc,y1,dd),(a,y1,dd)],roof or tex,sh)
    for p in(((a,b),(cc,b)),((cc,b),(cc,dd)),((cc,dd),(a,dd)),((a,dd),(a,b))):
        addq([(p[0][0],y0,p[0][1]),(p[1][0],y0,p[1][1]),(p[1][0],y1,p[1][1]),(p[0][0],y1,p[0][1])],tex,sh)
def obsbox(cx,cz,w,d):
    i0,i1=int((cx-w/2-x0)/OS),int((cx+w/2-x0)/OS)+1;j0,j1=int((cz-d/2-z0)/OS),int((cz+d/2-z0)/OS)+1
    OB[max(0,j0):min(OH,j1),max(0,i0):min(OW,i1)]=1
def obsband(za,zb,oa,ob_):
    for j in range(int((za-z0)/OS),int((zb-z0)/OS)+1):
        z=z0+j*OS+OS/2
        if j<0 or j>=OH:continue
        i0,i1=int((xc(z)+oa-x0)/OS),int((xc(z)+ob_-x0)/OS)+1;OB[j,max(0,i0):i1]=1
ZE=zs+LEN;ST0,ST1=zs+45,zs+62;TN0,TN1=zs+66,zs+88
# --- chao inteiro (grama) em faixas grandes
for tx in range(int(GW*CELL//T)+1):
    xa,xb=x0+tx*T,min(x0+(tx+1)*T,x0+GW*CELL)
    z=zs
    while z<ZE-1e-6:
        zb=min(ZE,max(z+.5,(math.floor((z-z0)/T+1e-9)+1)*T+z0))
        addq([(xa,GR,z),(xb,GR,z),(xb,GR,zb),(xa,GR,zb)],'grama');z=zb
# --- pista: asfalto, acostamento, canteiro, faixas
dz=.25;z=zs
zl=[zs+k*dz for k in range(int(LEN/dz)+1)]
for za,zb in zip(zl[:-1],zl[1:]):
    for sg in(1,-1):
        strip(za,zb,sg*MED,sg*CAR,RH,'asf');strip(za,zb,sg*CAR,sg*SHO,RH,'conc')
    strip(za,zb,-MED,MED,RH+.012,'concE')                         # canteiro central em concreto
    strip(za,zb,-MED-.004,-MED,RH,'concE');strip(za,zb,MED,MED+.004,RH,'concE')
# faixas: bordas brancas continuas, divisoria tracejada
for za,zb in zip(zl[:-1],zl[1:]):
    for sg in(1,-1):
        strip(za,zb,sg*(CAR-.008),sg*CAR,RH+.0008,'bra');strip(za,zb,sg*(MED+.004),sg*(MED+.012),RH+.0008,'ama')
for k in range(0,len(zl)-1,2):
    for sg in(1,-1):strip(zl[k],zl[k]+.12,sg*(.215-.004),sg*(.215+.004),RH+.0008,'bra')
# --- taludes (colinas e rampas do viaduto) fecham o vao entre a pista elevada e o chao
def fillh(z):e=EV(z);return Hh(z)+(e if e<.12 else 0)
for za,zb in zip(zl[:-1],zl[1:]):
    fa,fb=fillh(za),fillh(zb)
    if max(fa,fb)<.012:continue
    for sg in(1,-1):
        addq([(xc(za)+sg*SHO,RH+fa+GR*0,za),(xc(za)+sg*(SHO+.30),GR+0*fa,za),(xc(zb)+sg*(SHO+.30),GR,zb),(xc(zb)+sg*SHO,RH+fb,zb)],'grama',230)
# --- guard-rails (menos na entrada do posto), colisao
def rail_segments():
    out=[];a=zs
    for (p,q) in ((zs,ST0-.5),(ST1+.5,ZE)):out.append((p,q))
    return out
for sg in(1,-1):
    segs=[(zs,ZE)] if sg<0 else rail_segments()
    for a,b in segs:
        if TN0-1<b and a<TN1+1 and False:pass
        k0=int((a-zs)/dz);k1=int((b-zs)/dz)
        for k in range(k0,k1):
            za,zb=zl[k],zl[k+1]
            if TN0<=za<TN1:continue
            wall(za,zb,sg*RAIL,RH,RH+.035,'rail');strip(za,zb,sg*(RAIL-.01),sg*(RAIL+.01),RH+.035,'rail')
        obsband(max(a,zs),min(b,ZE),sg*(RAIL-.02),sg*(RAIL+.03)) if True else 0
# canteiro: colisao leve (barreira de concreto)
obsband(zs+2,ZE,-MED,MED)
# --- tunel
for k in range(int((TN0-zs)/dz),int((TN1-zs)/dz)):
    za,zb=zl[k],zl[k+1]
    for sg in(1,-1):wall(za,zb,sg*.56,RH,.23,'concE',150)
    strip(za,zb,-.56,.56,.23,'teto',110)
    for sg in(1,-1):wall(za,zb,sg*.55,RH,RH+.06,'bra',170)
    if k%4==0:
        for sg in(-.25,.25):strip(za,za+.1,sg-.015,sg+.015,.228,'lamp',255)
obsband(TN0,TN1,-.62,-.54);obsband(TN0,TN1,.54,.62)
for sg in(1,-1):                                        # portais
    for zz in(TN0,TN1):box(xc(zz)+sg*.62,zz,.1,.14,RH,.3,'concE')
for zz in(TN0,TN1):
    strip(zz-.06,zz+.06,-.6,.6,.3,'concE');addq([(xc(zz)-.6,.23,zz),(xc(zz)+.6,.23,zz),(xc(zz)+.6,.3,zz),(xc(zz)-.6,.3,zz)],'concE')
# sombra do teto (shadow heightfield) e altura no tunel
# --- posto de gasolina (lado +): pista de acesso, patio, loja, cobertura, bombas
zc=(ST0+ST1)/2;xp=xc(zc)
strip(ST0,ST1,SHO,SHO+.85,RH,'conc')
for zz in(ST0+1.0,ST0+4.2,ST1-4.2,ST1-1.0):pass
box(xp+1.18,zc,.26,.9,RH,.14,'lojaP',255,'teto')
box(xp+1.18-.14,zc,.012,.7,RH+.02,.1,'vidro')
for zz in(zc-4,zc,zc+4):box(xp+.72,zz,.03,.03,RH,.15,'poste');obsbox(xp+.72,zz,.06,.06)
box(xp+.72,zc,.34,1.0,.15,.17,'telhaV',255,'bra')             # cobertura
box(xp+.72,zc-.5,.34,.01,.145,.19,'azul')
for zz in(zc-2,zc+2):
    box(xp+.72,zz,.05,.06,RH,.07,'bomba');obsbox(xp+.72,zz,.08,.09)
obsbox(xp+1.18,zc,.28,.92)
box(xp+.42,ST0-2,.012,.012,RH,.2,'poste')
# --- postes de luz (canteiro) e arvores e placas
for k in range(0,int(LEN/1.2)):
    z=zs+2+k*1.2
    if TN0-.2<z<TN1+.2:continue
    cx=xc(z);hr=HR(z);box(cx,z,.02,.02,RH+hr,.2+hr,'poste');box(cx,z,.07,.03,.2+hr,.212+hr,'lamp');obsbox(cx,z,.05,.05)
rng=np.random.RandomState(11)
for k in range(260):
    z=zs+3+rng.rand()*(LEN-6)
    if TN0-1<z<TN1+1:continue
    sg=rng.choice([-1,1]);o=sg*(.62+rng.rand()*1.8)
    if sg>0 and ST0-1<z<ST1+1 and o<1.5:continue
    cx=xc(z)+o;h=.07+rng.rand()*.06
    box(cx,z,.02,.02,GR,h,'tronco');tr=.09+rng.rand()*.05;box(cx,z,tr,tr,h,h+tr,'folha' if rng.rand()<.6 else 'folha2');obsbox(cx,z,.04,.04)
for zz in(zs+20,zs+95):                                  # placas verdes sobre o acostamento
    cx=xc(zz)+.58;box(cx,zz,.015,.02,GR,.12,'poste');box(cx,zz,.16,.015,.09,.16,'placa');obsbox(cx,zz,.04,.04)
# --- viaduto: face inferior do tabuleiro, pilares, via transversal embaixo
for za,zb in zip(zl[:-1],zl[1:]):
    if EV((za+zb)/2)>.06:
        strip(za,zb,-SHO-.02,SHO+.02,-.03,'concE',120)
        for sg in(1,-1):wall(za,zb,sg*(SHO+.02),-.03,.0,'concE',140)
for zz in np.arange(zs+104,zs+121,3.4):
    for o in(-.58,0,.58):
        cx=xc(zz)+o;box(cx,zz,.05,.05,GR,RH+EV(zz)-.03,'concE');obsbox(cx,zz,.07,.07)
zx=zs+112                                                         # via transversal sob o viaduto
for za in np.arange(zx-.3,zx+.3,.25):
    addq([(xc(zx)-1.6,GR+.004,za),(xc(zx)+1.6,GR+.004,za),(xc(zx)+1.6,GR+.004,za+.25),(xc(zx)-1.6,GR+.004,za+.25)],'asf')
for xo in np.arange(-1.6,1.6,.25):
    addq([(xc(zx)+xo,GR+.0052,zx-.004),(xc(zx)+xo+.12,GR+.0052,zx-.004),(xc(zx)+xo+.12,GR+.0052,zx+.004),(xc(zx)+xo,GR+.0052,zx+.004)],'bra')
# barreira de fim do prototipo
box(xc(ZE-.2),ZE-.2,1.4,.1,RH,.1,'telhaV');obsbox(xc(ZE-.2),ZE-.2,1.5,.2);obsband(ZE-.6,ZE,-2,2)
# ---- grid / road / top (raster) ----
G[0,GH0:]=int(GR*1000)
Zc=z0+(np.arange(GH0,GH)+.5)*CELL;Xc=x0+(np.arange(GW)+.5)*CELL
XCz=np.array([xc(z) for z in Zc]);off=np.abs(Xc[None,:]-XCz[:,None])
HRz=np.array([Hh(z) for z in Zc]);EVz=np.array([EV(z) for z in Zc]);HRc=(HRz+EVz)[:,None]
road_h=(RH+HRz)[:,None]+0*off                                    # altura do chao na pista (colinas)
slope=np.clip(1-(off-SHO)/.30,0,1)*((off>=SHO)&(off<SHO+.30))*(HRz[:,None]*(1)+np.where(EVz[:,None]<.12,EVz[:,None],0))  # talude
Gh=np.where(off<SHO,road_h,GR+slope)
Gh=np.where(off<MED,road_h+.012,Gh)
vi=(EVz[:,None]>.04)&(off<SHO+.02)                                 # sob o viaduto: chao normal; tabuleiro na camada 1
Gh=np.where(vi,GR,Gh)
G[0,GH0:]=np.round(Gh*1000).astype(np.int16)
deck=(EVz[:,None]>.002)&(off<SHO)
G[1,GH0:][deck]=np.round((RH+HRc+0*off)[deck]*1000).astype(np.int16)
RD[GH0:][(off>MED)&(off<CAR)]=1
TPd=(EVz[:,None]>.04)&(off<SHO+.02)
inpost=(Zc[:,None]>=ST0)&(Zc[:,None]<=ST1)&(Xc[None,:]-XCz[:,None]>SHO)&(Xc[None,:]-XCz[:,None]<SHO+.85);G[0,GH0:][inpost]=int(RH*1000)
tun=(Zc[:,None]>=TN0)&(Zc[:,None]<=TN1)&(off<.56)
TPv=np.full((N,GW),21,np.uint8);TPv[tun]=int((.23+.2)/2.4*255);TPv[TPd]=np.clip((RH+HRc+.2+0*off)[TPd]/2.4*255,0,255).astype(np.uint8);TP[GH0:]=TPv
# emenda: preenche solo/pista nas ultimas linhas do mapa original (so onde esta vazio) para o carro passar sem parede
for j in range(GH0-40,GH0):
    z=z0+(j+.5)*CELL;o=np.abs(Xc-BASE)
    m=(o<.4)&(G[0,j]==-32768);G[0,j][m]=int(RH*1000)
    if j>=GH0-14:
        m2=(o<.45);G[0,j][m2]=int(RH*1000);G[1:,j][:,m2]=-32768
    r=(o<.3)&(RD[j]==0);RD[j][r]=1
# ---- escreve ----
gb=G.tobytes();open(M+'/grid.wav','wb').write(gb[:12000000]);open(M+'/grid2.wav','wb').write(gb[12000000:]);TP.tofile(M+'/top.wav')
np.packbits(RD.reshape(-1)).tofile(M+'/road.wav');np.packbits(OB.reshape(-1)).tofile(M+'/obs.wav')
nt=0
for (tx,tz),Q in sorted(quads.items()):
    for s in range(0,len(Q),12000):
        qs=Q[s:s+12000];P=np.array([p for q in qs for p in q[0]],np.float64);nv=len(P)
        U=np.array([UV[q[1]] for q in qs for _ in range(4)]);SH=np.array([q[2] for q in qs for _ in range(4)],np.uint8)
        mn=P.min(0);ext=np.maximum(P.max(0)-mn,1e-6)
        qq=np.round((P-mn)/ext*65535).astype(np.uint16);qu=np.round(U*65535).astype(np.uint16)
        ii=np.array([[4*m,4*m+1,4*m+2,4*m,4*m+2,4*m+3,4*m+2,4*m+1,4*m,4*m+3,4*m+2,4*m] for m in range(nv//4)],np.uint16).reshape(-1)
        name='r_%d_%d_%d.wav'%(tx,tz,s//12000)
        with open(M+'/'+name,'wb') as f:
            f.write(struct.pack('<II',nv,len(ii)));f.write(qq.tobytes());f.write(qu.tobytes());f.write(SH.tobytes());f.write(b'\0'*((4-nv%4)%4));f.write(ii.tobytes())
        c['tiles'].append(dict(f=name,tx=tx,tz=tz,mn=mn.round(5).tolist(),ext=ext.round(5).tolist(),nv=nv,ni=len(ii)));nt+=1
c['GH']=GH;c['OH']=OH;json.dump(c,open(M+'/tiles.json','w'))
# ---- vias (transito) ----
v=json.load(open(M+'/vias.json'))
if not v.get('ext'):
    n0=len(v['nodes']);pts=[[round(xc(z),3),round(z,3)] for z in np.arange(zs+.5,ZE-1.5,1.0)]
    v['nodes']+=[[pts[0][0],pts[0][1],2],[pts[-1][0],pts[-1][1],1]]
    v['edges'].append({'a':913,'b':n0,'w':.9,'p':[[-59.292,220.436],[xc(zs-.8),zs-.8]]+pts[:1]})
    v['edges'].append({'a':n0,'b':n0+1,'w':.9,'p':pts});v['ext']=True
    json.dump(v,open(M+'/vias.json','w'))
print('tiles r_:',nt,'GH',GH,'OH',OH,'z fim',ZE)
