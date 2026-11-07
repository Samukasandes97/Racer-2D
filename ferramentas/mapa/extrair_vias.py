"""Extrai a rede de ruas do mapa (esqueleto do chao dirigivel) -> vias.json
Uso: python3 extrair_vias.py <pasta do mapa convertido (grid.wav, tiles.json)> <groundcol.npy> <saida vias.json> [overlay.png]
Cada via: pontos (x,z) do eixo, largura (unidades), classe e limite de velocidade; nos = cruzamentos."""
import sys,json,numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt,label,binary_closing,binary_opening
from skimage.morphology import skeletonize
D,GC,OUT=sys.argv[1:4];OV=sys.argv[4] if len(sys.argv)>4 else None
c=json.load(open(D+'/tiles.json'));GW,GH,L,CELL=c['GW'],c['GH'],c['LAY'],c['CELL'];x0,z0=c['x0'],c['z0']
g=np.fromfile(D+'/grid.wav',np.int16).reshape(L,GH,GW)[0]
col=np.load(GC).astype(int)
ground=(g!=-32768)&(np.abs(g)<60)                         # rente ao chao (ruas, calcadas); sem rampas/telhados
green=(col[:,:,1]>col[:,:,0]+6)&(col[:,:,1]>col[:,:,2]+10)
ground&=~green
ground=binary_closing(ground,iterations=2)
lab,n=label(ground);sz=np.bincount(lab.ravel());keep=np.isin(lab,np.where(sz>1600)[0])&(lab>0);ground=keep
dist=distance_transform_edt(ground)
core=ground&(dist>=2.0)
core=core
sk=skeletonize(core)
print('skeleton px',int(sk.sum()))
# ---- grafo de pixels
ys,xs=np.where(sk);idx={(y,x):i for i,(y,x) in enumerate(zip(ys,xs))}
nb=[[(y+dy,x+dx) for dy in(-1,0,1) for dx in(-1,0,1) if(dy or dx)and(y+dy,x+dx)in idx] for y,x in zip(ys,xs)]
deg=np.array([len(a) for a in nb])
isnode=(deg!=2)
# juntar pixels de cruzamento vizinhos em um unico no
nodeid=-np.ones(len(ys),int);nodes=[]
for i in np.where(isnode)[0]:
    if nodeid[i]>=0:continue
    st=[i];comp=[]
    nodeid[i]=len(nodes)
    while st:
        a=st.pop();comp.append(a)
        for q in nb[a]:
            j=idx[q]
            if isnode[j] and nodeid[j]<0:nodeid[j]=len(nodes);st.append(j)
    nodes.append(comp)
print('nos',len(nodes))
def cen(comp):return np.array([np.mean([ys[i] for i in comp]),np.mean([xs[i] for i in comp])])
edges=[];seen=set()
for ni,comp in enumerate(nodes):
    for a in comp:
        for q in nb[a]:
            j=idx[q]
            if isnode[j] and nodeid[j]==ni:continue
            if (a,j) in seen:continue
            path=[a,j];prev=a;cur=j
            while not isnode[cur]:
                nxt=[idx[r] for r in nb[cur] if idx[r]!=prev]
                if not nxt:break
                prev,cur=cur,nxt[0];path.append(cur)
                if len(path)>5000:break
            seen.add((a,j));seen.add((path[-1],path[-2]))
            if isnode[cur]:
                e=nodeid[cur]
                if e==ni and len(path)<12:continue
                edges.append((ni,e,path))
print('arestas brutas',len(edges))
# ---- remove duplicadas (mesmo par/caminho invertido) e podar becos curtos
def length(path):return len(path)*CELL
def key(e):return (min(e[0],e[1]),max(e[0],e[1]),len(e[2]))
uniq={}
for e in edges:uniq.setdefault(key(e),e)
edges=list(uniq.values())
for _ in range(3):
    dg=np.zeros(len(nodes),int)
    for a,b,p in edges:dg[a]+=1;dg[b]+=1
    edges=[e for e in edges if not((dg[e[0]]==1 or dg[e[1]]==1) and length(e[2])<1.6)]
dg=np.zeros(len(nodes),int)
for a,b,p in edges:dg[a]+=1;dg[b]+=1
used=sorted(set([e[0] for e in edges]+[e[1] for e in edges]));remap={n_:i for i,n_ in enumerate(used)}
def rdp(P,eps):
    if len(P)<3:return P
    a,b=P[0],P[-1];ab=b-a;L2=(ab**2).sum()
    t=np.clip(((P-a)@ab)/L2,0,1) if L2>0 else np.zeros(len(P));d=np.linalg.norm(P-(a+t[:,None]*ab),axis=1)
    k=int(np.argmax(d))
    if d[k]>eps:return np.vstack([rdp(P[:k+1],eps)[:-1],rdp(P[k:],eps)])
    return np.vstack([a,b])
def w2(y,x):return (z0+(y+.5)*CELL, x0+(x+.5)*CELL)
out_nodes=[]
for n_ in used:
    cy,cx=cen(nodes[n_]);out_nodes.append([round(x0+(cx+.5)*CELL,3),round(z0+(cy+.5)*CELL,3),int(dg[n_])])
out_edges=[]
for a,b,p in edges:
    pts=np.array([[xs[i],ys[i]] for i in p],float)
    pts=np.array([[x0+(x+.5)*CELL,z0+(y+.5)*CELL] for x,y in pts])
    # ancora nas posicoes dos nos
    pts[0]=out_nodes[remap[a]][:2];pts[-1]=out_nodes[remap[b]][:2]
    wd=np.median([dist[ys[i],xs[i]] for i in p])*2*CELL
    P=rdp(pts,0.06)
    out_edges.append(dict(a=remap[a],b=remap[b],w=round(float(wd),3),p=np.round(P,3).tolist()))
# ---- pos-processamento: junta nos muito proximos (um cruzamento = um no), tira becos, poda pontas curtas
from scipy.spatial import cKDTree
N=len(out_nodes);par=list(range(N))
def fd(a):
    while par[a]!=a:par[a]=par[par[a]];a=par[a]
    return a
tr=cKDTree([n[:2] for n in out_nodes])
for a,b in tr.query_pairs(0.55):par[fd(a)]=fd(b)
groups={}
for i_ in range(N):groups.setdefault(fd(i_),[]).append(i_)
newid={};NN=[]
for r,mem in groups.items():
    pos=np.mean([out_nodes[m][:2] for m in mem],axis=0);newid[r]=len(NN);NN.append([round(float(pos[0]),3),round(float(pos[1]),3)])
ed=[]
for e in out_edges:
    a=newid[fd(e['a'])];b=newid[fd(e['b'])]
    if e['w']<0.5:continue                                  # vielas/calcadas
    P=np.array(e['p']);P[0]=NN[a];P[-1]=NN[b]
    if a==b:continue
    ed.append(dict(a=a,b=b,w=e['w'],p=P.tolist()))
def elen(e):
    P=np.array(e['p']);return float(np.linalg.norm(np.diff(P,axis=0),axis=1).sum())
for _ in range(4):
    dg=np.zeros(len(NN),int)
    for e in ed:dg[e['a']]+=1;dg[e['b']]+=1
    ed=[e for e in ed if not((dg[e['a']]==1 or dg[e['b']]==1) and elen(e)<1.2)]
# duplicadas (mesmo par de nos): mantem a mais larga
best={}
for e in ed:
    k=(min(e['a'],e['b']),max(e['a'],e['b']));
    if k not in best or elen(e)<elen(best[k]) :best[k]=e
ed=list(best.values())
dg=np.zeros(len(NN),int)
for e in ed:dg[e['a']]+=1;dg[e['b']]+=1
used=sorted(set(e['a'] for e in ed)|set(e['b'] for e in ed));rm={n_:i for i,n_ in enumerate(used)}
out_nodes=[NN[n_]+[int(dg[n_])] for n_ in used]
# ruas retas: se o caminho nao se afasta mais de 0,12 da corda entre os dois nos, vira reta (grade urbana e ortogonal)
def straighten(P):
    P=np.array(P);a,b=P[0],P[-1];ab=b-a;L2=(ab**2).sum()
    if L2==0:return P
    t=np.clip(((P-a)@ab)/L2,0,1);d=np.linalg.norm(P-(a+t[:,None]*ab),axis=1)
    return np.array([a,b]) if d.max()<0.12 else P
out_edges=[dict(a=rm[e['a']],b=rm[e['b']],w=e['w'],p=np.round(straighten(e['p']),3).tolist()) for e in ed]
print('depois da limpeza: nos',len(out_nodes),'arestas',len(out_edges),'cruzamentos(grau>=3)',sum(1 for n_ in out_nodes if n_[2]>=3))
ws=np.array([e['w'] for e in out_edges]);print('arestas',len(out_edges),'largura pcts',np.percentile(ws,[5,25,50,75,95]).round(2))
json.dump(dict(nodes=out_nodes,edges=out_edges),open(sys.argv[3],'w'))
if OV:
    im=np.zeros((GH,GW,3),np.uint8);im[ground]=(60,60,70);im[sk]=(255,80,80)
    for e in out_edges:
        for x,z in e['p']:
            im[int((z-z0)/CELL),int((x-x0)/CELL)]=(255,255,0)
    for x,z,d_ in out_nodes:
        j=int((z-z0)/CELL);i=int((x-x0)/CELL);im[max(0,j-1):j+2,max(0,i-1):i+2]=(0,255,0) if d_>=3 else (0,160,255)
    Image.fromarray(im).save(OV)
