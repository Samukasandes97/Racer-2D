"""Gera camadas derivadas do cockpit a partir da foto original (que NAO e alterada).
Saida: demos/corrida-shibuya/img/cockpit/*.png + cockpit.json  (coordenadas em px do jogo)"""
import cv2, json, sys, numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[2]
SRC=R/'arte/referencias/cockpit-interior/originais/interior_01.jpg'
OUT=R/'demos/corrida-shibuya/img/cockpit'; OUT.mkdir(parents=True,exist_ok=True)
DEBUG=len(sys.argv)>1
SC=0.34; PX=100; PY=15          # escala do jogo e padding (reflexo) p/ sobra de balanco
im0=cv2.imread(str(SRC)); H0,W0=im0.shape[:2]
im=cv2.copyMakeBorder(im0,PY,PY,PX,PX,cv2.BORDER_REPLICATE)
H,W=im.shape[:2]
wgt=np.full((H,W),.3,np.float32); wgt[PY:PY+H0,PX:PX+W0]=1; wgt=cv2.GaussianBlur(wgt,(0,0),9)
wgt[PY+30:PY+H0-30,PX+40:PX+W0-40]=1
im=(im*wgt[...,None]).astype(np.uint8)
def P(pts): return np.array([(x+PX,y+PY) for x,y in pts],np.int32)
def poly(pts):
    m=np.zeros((H,W),np.uint8); cv2.fillPoly(m,[P(pts)],255); return m
HUB=(630,640)
# --- geometria (px da foto original) ---
GLASS=[(188,112),(350,103),(560,100),(1090,100),(1110,106),(1150,122),(1198,135),(1190,200),(1160,330),(1092,430),(800,430),(290,432),(262,380),(235,300),(215,200)]
MIRROR=[(566,132),(792,132),(796,150),(792,188),(770,196),(585,196),(566,186)]
SIDEM=[(-PX-5,368),(92,372),(96,420),(70,440),(-PX-5,444)]
WINL=[(-PX-5,80),(45,72),(75,115),(110,205),(135,290),(152,350),(-PX-5,352)]
WINR=[(1228,118),(1264+PX+5,100),(1264+PX+5,330),(1236,320),(1218,230)]
RING=dict(c=HUB,r0=212,r1=274)
SPOKES=[[(440,585),(570,598),(572,690),(446,650)],[(818,585),(690,598),(688,690),(812,650)],[(598,700),(662,700),(670,843),(590,843)]]
GLOVE_L=[(318,552),(340,548),(362,575),(380,590),(405,585),(425,580),(442,592),(444,612),(432,632),(436,655),(430,680),(432,712),(424,738),(405,728),(388,745),(372,768),(345,778),(300,764),(258,752),(258,735),(264,640),(285,625),(300,600)]
GLOVE_R=[(945,560),(900,548),(880,560),(855,585),(830,585),(815,598),(812,620),(822,640),(830,670),(836,700),(852,730),(868,742),(880,765),(905,778),(950,768),(1000,752),(1004,735),(990,700),(985,640),(960,610),(950,580)]
ARM_L=[(190,760),(258,752),(300,764),(345,778),(372,768),(380,843),(190,843)]
ARM_R=[(1070,760),(1004,752),(950,768),(905,778),(880,765),(870,843),(1070,843)]
GAUGES=dict(L=(541,517,64),R=(708,517,66))
NEEDLE=dict(L=((560,509),(507,546)),R=((727,508),(673,543)))
PIVOT=dict(L=(547,519),R=(708,519))
# mascaras
ring=np.zeros((H,W),np.uint8)
cv2.circle(ring,(HUB[0]+PX,HUB[1]+PY),RING['r1'],255,-1); cv2.circle(ring,(HUB[0]+PX,HUB[1]+PY),RING['r0'],0,-1)
hub=np.zeros((H,W),np.uint8); cv2.circle(hub,(HUB[0]+PX,HUB[1]+PY),72,255,-1)
spk=np.zeros((H,W),np.uint8)
for s in SPOKES: cv2.fillPoly(spk,[P(s)],255)
wheel=ring|hub|spk
gl=poly(GLOVE_L)|poly(GLOVE_R)
b_,g_,r_=[im[...,i].astype(int) for i in range(3)]
skin=((r_>140)&(r_>b_+35)&(r_>g_+10)).astype(np.uint8)*255
skin=cv2.morphologyEx(skin,cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))
arm=(poly(ARM_L)|poly(ARM_R))&skin
# agulhas baked (laranja) dentro dos mostradores
needle=np.zeros((H,W),np.uint8)
for k,(a,b) in NEEDLE.items(): cv2.line(needle,(a[0]+PX,a[1]+PY),(b[0]+PX,b[1]+PY),255,9)
glass=poly(GLASS); mir=poly(MIRROR); sidem=poly(SIDEM)|poly(WINL)|poly(WINR)
if DEBUG:
    d=im.copy()
    for m,c in((wheel,(0,0,255)),(gl,(0,255,0)),(arm,(255,0,0)),(needle,(0,255,255)),(glass,(255,255,0)),(mir,(255,0,255)),(sidem,(255,0,255))):
        d[m>0]=(0.5*d[m>0]+0.5*np.array(c)).astype(np.uint8)
    for k,(x,y,r) in GAUGES.items(): cv2.circle(d,(x+PX,y+PY),r,(255,255,255),1)
    cv2.imwrite(DEBUG and sys.argv[1],d); sys.exit()
# --- fundo limpo ---
work=im.copy()
dark=np.array([36,34,32],np.uint8)
for m in (glass,mir,sidem): work[m>0]=dark
rm=cv2.dilate(wheel|gl|arm|needle,np.ones((7,7),np.uint8))
work=cv2.inpaint(work,rm,7,cv2.INPAINT_TELEA)
bl=cv2.GaussianBlur(work,(0,0),6); low=np.zeros((H,W),np.uint8); low[PY+655:,:]=255
sel=(rm>0)&(low>0); work[sel]=(bl[sel]*.5).astype(np.uint8)
bgA=np.full((H,W),255,np.uint8)
hole=cv2.dilate(glass|mir|sidem,np.ones((3,3),np.uint8))
bgA[hole>0]=0
bgA=cv2.GaussianBlur(bgA,(3,3),0)
def save(img,alpha,name,box=None):
    x0,y0,x1,y1=box or (0,0,W,H)
    c=np.dstack([img[y0:y1,x0:x1],alpha[y0:y1,x0:x1]])
    c=cv2.resize(c,(max(1,round((x1-x0)*SC)),max(1,round((y1-y0)*SC))),interpolation=cv2.INTER_AREA)
    cv2.imwrite(str(OUT/name),c)
    return (x0*SC,y0*SC,c.shape[1],c.shape[0])
save(work,bgA,'bg.png')
# --- volante + maos (rigido): recorte quadrado em volta do cubo p/ girar facil ---
# aro sob as luvas: copia do trecho limpo do proprio aro (rotacao de 60 graus em torno do cubo), sem borrao
hx0,hy0=HUB[0]+PX,HUB[1]+PY
ann=np.zeros((H,W),np.uint8); cv2.circle(ann,(hx0,hy0),278,255,-1); cv2.circle(ann,(hx0,hy0),208,0,-1)
gD=cv2.dilate(poly(GLOVE_L)|poly(GLOVE_R),np.ones((9,9),np.uint8))&ann
xs=np.arange(W)[None,:]*np.ones((H,1))
rotCW=cv2.warpAffine(im,cv2.getRotationMatrix2D((hx0,hy0),-60,1),(W,H),flags=cv2.INTER_LINEAR)
rotCCW=cv2.warpAffine(im,cv2.getRotationMatrix2D((hx0,hy0),60,1),(W,H),flags=cv2.INTER_LINEAR)
wimg=im.copy()
selR=(gD>0)&(xs>hx0); selL=(gD>0)&(xs<=hx0)
wimg[selR]=rotCW[selR]; wimg[selL]=rotCCW[selL]
rig=cv2.dilate(wheel,np.ones((3,3),np.uint8))
hx,hy=HUB[0]+PX,HUB[1]+PY; half=330
box=(hx-half,hy-half,hx+half,min(hy+half,H)) 
wb=(hx-half,hy-half,hx+half,hy+half)
HUBP=(hx,hy)
pad=cv2.copyMakeBorder(im,0,max(0,wb[3]-H),0,0,cv2.BORDER_REFLECT_101)
rigp=cv2.copyMakeBorder(rig,0,max(0,wb[3]-H),0,0,cv2.BORDER_CONSTANT,value=0)
padw=cv2.copyMakeBorder(wimg,0,max(0,wb[3]-H),0,0,cv2.BORDER_REFLECT_101)
save(padw,rigp,'wheel.png',wb)
def bbox(m,pd=3):
    ys,xs=np.where(m>0);return (xs.min()-pd,ys.min()-pd,xs.max()+pd,ys.max()+pd)
glL=cv2.dilate(poly(GLOVE_L),np.ones((3,3),np.uint8)); glR=cv2.dilate(poly(GLOVE_R),np.ones((3,3),np.uint8))
bgL=bbox(glL); bgR=bbox(glR)
save(im,glL,'gloveL.png',bgL); save(im,glR,'gloveR.png',bgR)
# antebracos (pele abaixo da luva): recortes por lado
ab=lambda pts:(min(p[0] for p in pts)+PX-6,min(p[1] for p in pts)+PY-6,max(p[0] for p in pts)+PX+6,H)
armL=cv2.dilate(poly(ARM_L)&skin,np.ones((3,3),np.uint8)); armR=cv2.dilate(poly(ARM_R)&skin,np.ones((3,3),np.uint8))
bL=ab(ARM_L); bR=ab(ARM_R)
save(im,armL,'armL.png',bL); save(im,armR,'armR.png',bR)
# --- config em px do jogo (relativo ao bg) ---
g=lambda x,y:[round((x+PX)*SC,1),round((y+PY)*SC,1)]
gp=lambda pts:[g(x,y) for x,y in pts]
cfg=dict(size=[round(W*SC),round(H*SC)],sc=SC,hub=g(*HUB),wheelBox=[round(wb[0]*SC,1),round(wb[1]*SC,1)],
 wheelSize=round(2*half*SC),
 gloveL=dict(box=[round(bgL[0]*SC,1),round(bgL[1]*SC,1)]),gloveR=dict(box=[round(bgR[0]*SC,1),round(bgR[1]*SC,1)]),
 armL=dict(box=[round(bL[0]*SC,1),round(bL[1]*SC,1)],wrist=g(310,762)),
 armR=dict(box=[round(bR[0]*SC,1),round(bR[1]*SC,1)],wrist=g(940,762)),
 glass=gp(GLASS),mirror=gp(MIRROR),side=gp(SIDEM),
 gaugeL=g(GAUGES['L'][0],GAUGES['L'][1])+[round(GAUGES['L'][2]*SC,1)],
 gaugeR=g(GAUGES['R'][0],GAUGES['R'][1])+[round(GAUGES['R'][2]*SC,1)],
 lampTurnL=g(445,517),lampTurnR=g(808,517),lampRed=g(440,560),
 needle=dict(L=dict(p=g(*PIVOT['L']),len=round(52*SC,1),tail=round(15*SC,1),a0=146,a1=402),R=dict(p=g(*PIVOT['R']),len=round(52*SC,1),tail=round(15*SC,1),a0=146,a1=402)),
 radio=g(268,603),heat=[g(258,508),g(298,508),g(342,508)])
(OUT/'cockpit.json').write_text(json.dumps(cfg))
print('ok',cfg['size'])
