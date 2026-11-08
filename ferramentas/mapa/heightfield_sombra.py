"""Mapa de alturas (topo da geometria por celula) para sombras em tempo real.
Uso: python3 heightfield_sombra.py <mapdir>  -> <mapdir>/top.wav (8 bits, 1 byte/celula, mesmo GW x GH do grid) e acrescenta TOP em tiles.json"""
import sys,json,numpy as np
from scipy.ndimage import distance_transform_edt
D=sys.argv[1];c=json.load(open(D+'/tiles.json'));GW,GH,L,CELL=c['GW'],c['GH'],c['LAY'],c['CELL'];x0,z0=c['x0'],c['z0']
YMIN,YMAX=-0.2,2.2
top=np.full((GH,GW),-9.0,np.float32)
def put(x,y,z):
    i=((x-x0)/CELL).astype(int);j=((z-z0)/CELL).astype(int);ok=(i>=0)&(i<GW)&(j>=0)&(j<GH)
    np.maximum.at(top,(j[ok],i[ok]),y[ok])
for t in c['tiles']:
    b=open(D+'/'+t['f'],'rb').read();nv,ni=np.frombuffer(b[:8],np.uint32)
    q=np.frombuffer(b,np.uint16,nv*3,8).reshape(-1,3).astype(np.float32)/65535
    ind=np.frombuffer(b,np.uint16,ni,8+nv*6+nv*4+nv+((4-nv%4)%4)).reshape(-1,3).astype(int)
    P=np.array(t['mn'],np.float32)+q*np.array(t['ext'],np.float32)
    put(P[:,0],P[:,1],P[:,2])
    A,B,C=P[ind[:,0]],P[ind[:,1]],P[ind[:,2]]
    for w in ((A+B+C)/3,(A+B)/2,(B+C)/2,(A+C)/2,(A*.75+B*.125+C*.125),(B*.75+A*.125+C*.125),(C*.75+A*.125+B*.125)):put(w[:,0],w[:,1],w[:,2])
has=top>-8
void=(np.fromfile(D+'/grid.wav',np.int16).reshape(L,GH,GW)[0]==-32768)
# celulas de predio (vazias) sem amostra: herdam o topo do vizinho mais proximo que tem
need=void&~has
_,(ij,ii)=distance_transform_edt(~has,return_indices=True)
top=np.where(need,top[ij,ii],top)
top=np.where(top<-8,0,top)
# suaviza 1 celula (max) para nao ter buracos entre amostras de parede
from scipy.ndimage import maximum_filter
top=maximum_filter(top,size=3)
q8=np.clip((top-YMIN)/(YMAX-YMIN)*255,0,255).astype(np.uint8)
q8.tofile(D+'/top.wav')
c['TOP']={'ymin':YMIN,'ymax':YMAX};json.dump(c,open(D+'/tiles.json','w'),separators=(',',':'))
print('max top',float(top.max()),'cells>0.2',int((top>0.2).sum()))
from PIL import Image;Image.fromarray(q8).resize((GW//3,GH//3)).save('/tmp/t/top.png')
