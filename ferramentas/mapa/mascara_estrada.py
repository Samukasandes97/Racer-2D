"""Mascara de area dirigivel: corredor das ruas (vias.json engrossado) + trechos elevados (rampas/viadutos).
Uso: python3 mascara_estrada.py <mapdir>   -> grava <mapdir>/road.wav (1 bit por celula da grade, mesmo GW x GH do grid)"""
import sys,json,numpy as np,os
from PIL import Image,ImageDraw
D=sys.argv[1];c=json.load(open(D+'/tiles.json'));GW,GH,L,CELL=c['GW'],c['GH'],c['LAY'],c['CELL'];x0,z0=c['x0'],c['z0']
g=np.fromfile(D+'/grid.wav',np.int16).reshape(L,GH,GW)
v=json.load(open(D+'/vias.json'))
im=Image.new('L',(GW,GH),0);d=ImageDraw.Draw(im)
def P(p):return ((p[0]-x0)/CELL,(p[1]-z0)/CELL)
for e in v['edges']:
    wpx=(e['w']+1.4)/CELL
    pts=[P(p) for p in e['p']]
    d.line(pts,fill=255,width=int(wpx))
    r=wpx/2
    for q in (pts[0],pts[-1]):d.ellipse([q[0]-r,q[1]-r,q[0]+r,q[1]+r],fill=255)
m=np.array(im)>0
from scipy.ndimage import distance_transform_edt
im2=Image.new('L',(GW,GH),0);d2=ImageDraw.Draw(im2)
for e in v['edges']:d2.line([P(p) for p in e['p']],fill=255,width=1)
m|=distance_transform_edt(~(np.array(im2)>0))*CELL<=0.9   # tambem tudo a ate ~21 m do eixo de qualquer rua
elev=((g[0]>60)|(g[0]<-60))&(g[0]!=-32768)       # rampas e trechos altos/baixos no nivel 0
elev|=(g[1]!=-32768)&(g[1]>60)                   # viadutos (camada 1)
m|=elev
m&=(g[0]!=-32768)|(g[1]!=-32768)
np.packbits(m.ravel()).tofile(D+'/road.wav')
print('celulas dirigiveis',int(m.sum()),'de',int((g[0]!=-32768).sum()))
Image.fromarray((m*255).astype(np.uint8)).save('/tmp/t/road.png')
