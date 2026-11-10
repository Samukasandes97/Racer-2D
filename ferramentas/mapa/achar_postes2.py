import numpy as np,json
OBJ='/tmp/mapa/Chicago_Split/chicago_day_split.obj'
V=[];F=[];FM=[];mats={};cur=0
for l in open(OBJ,errors='ignore'):
    c=l[:2]
    if c=='v ':p=l.split();V.append((float(p[1]),float(p[2]),float(p[3])))
    elif l.startswith('usemtl'):cur=mats.setdefault(l.split()[1],len(mats))
    elif c=='f ':
        q=[int(t.split('/')[0])-1 for t in l.split()[1:]];F.append(q[:3]);FM.append(cur)
        if len(q)==4:F.append([q[0],q[2],q[3]]);FM.append(cur)
V=np.array(V);F=np.array(F);FM=np.array(FM);P=V[F];inv={v:k for k,v in mats.items()}
ext=P.max(1)-P.min(1);mnf=P.min(1)[:,1];mxf=P.max(1)[:,1]
m=(ext[:,1]>.07)&(np.maximum(ext[:,0],ext[:,2])<.05)&(mnf<.25)
print('faces finas',m.sum())
c=P[m].mean(1);top=mxf[m];bot=mnf[m];mm=FM[m]
key=np.round(c[:,[0,2]]/.05).astype(int)
d={}
for (kx,kz),(x,y,z),t,b,mt in zip(key,c,top,bot,mm):
    e=d.setdefault((kx,kz),[x,z,t,b,0,set()]);e[2]=max(e[2],t);e[3]=min(e[3],b);e[4]+=1;e[5].add(inv[mt])
L=[v for v in d.values()]
H=np.array([v[2]-v[3] for v in L]);print('postes unicos',len(L),np.histogram(H,bins=[.12,.2,.25,.3,.35,.4,.5,.7,1.5]))
np.save('/tmp/t/shafts.npy',np.array(L))
import sys
POLEMATS=set(sys.argv[1].split(',')) if len(sys.argv)>1 else set(mats)
RD=np.unpackbits(np.fromfile('../../demos/mundo-aberto/mapa/road.wav',np.uint8))[:1024*3116].reshape(3116,1024)[:1916]
out=[]
import collections
cnt=collections.Counter(next(iter(v[5])) for v in L if v[2]>=.2 and v[2]-v[3]>=.12);print(cnt.most_common(8))
for x,z,t,b,n,ms in L:
    if not(.14<=t<=.30 and 'page_0' in ms and t-b>=.1):continue
    ci,cj=int((x+111.975)/.1),int((z-32.0196)/.1)
    if RD[max(0,cj-6):cj+7,max(0,ci-6):ci+7].any():out.append([round(float(x),3),round(float(z),3),round(float(t),3)])
json.dump(out,open('../../demos/mundo-aberto/mapa/postes.json','w'),separators=(',',':'));print('postes.json',len(out))
