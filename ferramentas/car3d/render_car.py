"""Renderizador 3D minimo (numpy + PIL) do Honda laranja em estilo pixel-art com contorno.
Uso: python3 render_car.py <azimute_graus> <saida.png> [elevacao_graus]
azimute 0 = camera atras do carro, 90 = lado direito do carro, 180 = frente.
"""
import sys, math
import numpy as np
from PIL import Image

S = 0.00217            # px da referencia lateral -> metros
def X(px): return (px - 1000) * S
def Y(py): return (872 - py) * S

# --- perfil lateral (da referencia lateral) ---
TOP = [(105,705),(125,690),(135,600),(165,535),(215,445),(285,372),(420,338),(600,326),(900,325),
       (960,345),(1100,432),(1340,500),(1560,548),(1760,585),(1860,622),(1868,700),(1900,716)]
BOT = [(105,772),(180,792),(560,846),(1200,846),(1750,792),(1900,776)]
tx = np.array([X(p[0]) for p in TOP]); ty = np.array([Y(p[1]) for p in TOP])
bx = np.array([X(p[0]) for p in BOT]); by = np.array([Y(p[1]) for p in BOT])
XMIN, XMAX = X(105), X(1900)
WHEELS = [X(350), X(1365)]; WY = Y(748); TIRE_R = 128*S; RIM_R = 98*S

def ytop(x): return np.interp(x, tx, ty)
def ybot(x): return np.interp(x, bx, by)
def belt(x):  return np.where(x < X(260), Y(485), Y(520))

ORANGE=(226,110,28); DARK=(38,36,40); GLASS=(70,86,104); BRONZE=(150,98,50)
RED=(170,30,24); AMBER=(230,140,30); TIRE=(24,24,26); GRAY=(70,70,76); CHROME=(190,195,200)

tris = []   # (v0,v1,v2,color,region)
def add_quad(a,b,c,d,col,reg,flip=False):
    if flip: a,b,c,d = a,d,c,b
    tris.append((a,b,c,col,reg)); tris.append((a,c,d,col,reg))

def hw_at(x):
    h = 0.80 + 0.04*np.clip((x-XMIN)/(XMAX-XMIN),0,1)
    for wx in WHEELS:
        h += 0.17*math.exp(-((x-wx)/0.50)**4)   # flare largura dos paralamas
    return h

def section(x):
    yt, yb, bl = float(ytop(x)), float(ybot(x)), float(belt(x))
    hw = hw_at(x); roof_hw = hw*0.70 if yt > bl+0.05 else hw*0.97
    bl = min(bl, yt-0.02)
    pts = [(-hw*0.88,yb),( -hw,yb+0.07),(-hw,bl),(-roof_hw,yt-0.04),(-roof_hw*0.9,yt),
           (roof_hw*0.9,yt),(roof_hw,yt-0.04),(hw,bl),(hw,yb+0.07),(hw*0.88,yb)]
    return pts, bl

N = 150
xs = np.linspace(XMIN, XMAX, N)
secs = [section(x) for x in xs]

def color_for(c, nrm):
    x,y,z = c; yt = float(ytop(x)); bl = float(belt(x)); yb = float(ybot(x))
    az = abs(z)
    if nrm[0] < -0.5 and x < XMIN+0.08:                       # traseira
        if y < yb+0.13: return DARK,'bump'
        if Y(700)<y<Y(585) and 0.18<az<0.78: return (RED if az<0.55 else AMBER),'tail'
        if Y(640)>y>Y(560) and az<0.2: return DARK,'plate'
    if y < yb+0.12 and (x<XMIN+0.25 or x>XMAX-0.30): return DARK,'bump'
    if y < yb+0.13 and nrm[1] < -0.3: return DARK,'under'
    if y < Y(808) and X(560)<x<X(1200) : return DARK,'sill'
    if nrm[0] > 0.5 and x > XMAX-0.08:
        if abs(y-Y(668))<0.12 and az<0.62: return DARK,'grille'
    if y > bl+0.015 and y < yt-0.065 and X(290)<x<X(1345):
        if abs(x-X(635))<0.05 or abs(x-X(985))<0.04 or abs(x-X(345))<0.04: return ORANGE,'pillar'
        return GLASS,'glass'
    if x < X(300) and y > Y(485)+0.0 and y < yt-0.04 and nrm[0] < -0.2: return GLASS,'glass'
    return ORANGE,'body'

# --- carroceria por loft ---
for i in range(N-1):
    s0,_ = secs[i]; s1,_ = secs[i+1]
    for j in range(len(s0)):
        k = (j+1) % len(s0)
        a=(xs[i],s0[j][1],s0[j][0]); b=(xs[i+1],s1[j][1],s1[j][0])
        c=(xs[i+1],s1[k][1],s1[k][0]); d=(xs[i],s0[k][1],s0[k][0])
        add_quad(a,b,c,d,None,None)
body_raw = tris[:]; tris.clear()

def normal(v0,v1,v2):
    a=np.subtract(v1,v0); b=np.subtract(v2,v0); n=np.cross(a,b); l=np.linalg.norm(n)
    return n/l if l>1e-12 else n
def centroid(v0,v1,v2): return tuple(np.mean([v0,v1,v2],axis=0))

final=[]
for (v0,v1,v2,_,_) in body_raw:
    n = normal(v0,v1,v2); c = centroid(v0,v1,v2)
    # orienta normal para fora (centro do carro = eixo)
    ctr = np.array([c[0], (float(ytop(c[0]))+float(ybot(c[0])))/2, 0])
    if np.dot(n, np.array(c)-ctr) < 0:
        v1,v2 = v2,v1; n = -n
    col,reg = color_for(c,n)
    final.append((v0,v1,v2,col,reg))
# tampas frente/tras
for idx,sgn in ((0,-1),(N-1,1)):
    s,_ = secs[idx]; cen=(xs[idx], np.mean([p[1] for p in s]), 0.0)
    for j in range(len(s)):
        k=(j+1)%len(s)
        v0=cen; v1=(xs[idx],s[j][1],s[j][0]); v2=(xs[idx],s[k][1],s[k][0])
        n=normal(v0,v1,v2)
        if n[0]*sgn < 0: v1,v2=v2,v1; n=-n
        c=centroid(v0,v1,v2); col,reg=color_for(c,n)
        final.append((v0,v1,v2,col,reg))
tris[:] = final

def add_box(c, size, col, reg):
    cx,cy,cz=c; sx,sy,sz=[s/2 for s in size]
    V=[(cx+a*sx,cy+b*sy,cz+d*sz) for a in(-1,1) for b in(-1,1) for d in(-1,1)]
    idx=[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)]
    for q in idx:
        a,b,c_,d=[V[i] for i in q]
        n=normal(a,b,c_)
        if np.dot(n,np.subtract(centroid(a,b,c_),c))<0: a,b,c_,d=a,d,c_,b
        tris.append((a,b,c_,col,reg)); tris.append((a,c_,d,col,reg))

def add_cyl_x(c, r, length, col, reg, n=16):   # eixo ao longo de x
    cx,cy,cz=c
    for i in range(n):
        t0=2*math.pi*i/n; t1=2*math.pi*(i+1)/n
        a=(cx-length/2,cy+r*math.cos(t0),cz+r*math.sin(t0)); b=(cx+length/2,a[1],a[2])
        d=(cx-length/2,cy+r*math.cos(t1),cz+r*math.sin(t1)); c2=(cx+length/2,d[1],d[2])
        tris.append((a,b,c2,col,reg)); tris.append((a,c2,d,col,reg))
        tris.append(((cx+length/2,cy,cz),c2,b,col,reg))

def add_cyl_z(c, r, width, col, reg, n=28, spokes=False):  # roda: eixo ao longo de z
    cx,cy,cz=c
    for i in range(n):
        t0=2*math.pi*i/n; t1=2*math.pi*(i+1)/n
        p=lambda t,z:(cx+r*math.cos(t),cy+r*math.sin(t),z)
        a,b,d,c2=p(t0,cz-width/2),p(t0,cz+width/2),p(t1,cz-width/2),p(t1,cz+width/2)
        tris.append((a,b,c2,col,reg)); tris.append((a,c2,d,col,reg))
    return

def add_disc_z(c, r, z, col, reg, facing, n=28, spokes=0, hub=0.0):
    cx,cy,_=c
    for i in range(n):
        t0=2*math.pi*i/n; t1=2*math.pi*(i+1)/n
        v0=(cx,cy,z); v1=(cx+r*math.cos(t0),cy+r*math.sin(t0),z); v2=(cx+r*math.cos(t1),cy+r*math.sin(t1),z)
        nn=normal(v0,v1,v2)
        if nn[2]*facing<0: v1,v2=v2,v1
        cc=col
        if spokes:
            ang=(math.atan2(v1[1]-cy,v1[0]-cx)+math.pi)%(2*math.pi)
            seg=(ang/(2*math.pi)*spokes*2)
            cc = col if int(seg)%2==0 else DARK
        tris.append((v0,v1,v2,cc,reg))

# rodas
for wx in WHEELS:
    for side in (-1,1):
        zc = side*(hw_at(wx)-0.14)
        add_cyl_z((wx,WY,zc), TIRE_R, 0.30, TIRE, 'tire')
        zf = zc + side*0.15
        add_disc_z((wx,WY,0), TIRE_R, zf, TIRE, 'tire', side)
        add_disc_z((wx,WY,0), RIM_R, zf+side*0.004, BRONZE, 'rim', side, spokes=7)
        add_disc_z((wx,WY,0), RIM_R*0.22, zf+side*0.008, CHROME, 'hub', side)
# aerofolio, spoiler traseiro, difusor, escapes, faróis, alvo
add_box((X(330),Y(335),0), (0.40,0.035,1.12), DARK, 'spoiler')
add_box((XMIN+0.12,Y(782),0), (0.34,0.10,1.30), DARK, 'diffuser')
for zz in (-0.30,-0.18):
    add_cyl_x((XMIN-0.03,Y(790),zz), 0.045, 0.14, BRONZE, 'exh')
add_box((XMAX-0.10,Y(808),0), (0.45,0.04,1.55), DARK, 'splitter')
for zz in (-0.64,-0.46,0.46,0.64):
    add_cyl_x((XMAX+0.0,Y(668),zz), 0.085, 0.07, (205,215,225), 'lamp', n=14)
add_box((XMAX-0.015,Y(755),0), (0.10,0.11,1.58), DARK, 'bumper')
add_box((XMIN+0.01,Y(735),0), (0.12,0.10,1.62), DARK, 'rbumper')
# retrovisores
for sd in (-1,1):
    add_box((X(1010),Y(505),sd*(hw_at(X(1010))*0.70+0.12)), (0.10,0.10,0.15), DARK, 'mirror')

# sombra no chao
shadow=[(XMIN-0.2,0.002,-1.0),(XMAX+0.2,0.002,-1.0),(XMAX+0.2,0.002,1.0),(XMIN-0.2,0.002,1.0)]
tris.append((shadow[0],shadow[1],shadow[2],(188,188,196),'shadow'))
tris.append((shadow[0],shadow[2],shadow[3],(188,188,196),'shadow'))
tris.append((shadow[0],shadow[2],shadow[1],(188,188,196),'shadow'))
tris.append((shadow[0],shadow[3],shadow[2],(188,188,196),'shadow'))

# ---------------- render ----------------
def render(az_deg, out, el_deg=9.0, W=640, H=360, dist=7.2, scale=3):
    az=math.radians(az_deg); el=math.radians(el_deg)
    tgt=np.array([0.0,0.62,0.0])
    cam=tgt+dist*np.array([-math.cos(az)*math.cos(el), math.sin(el), math.sin(az)*math.cos(el)])
    f=tgt-cam; f/=np.linalg.norm(f); r=np.cross(f,[0,1,0]); r/=np.linalg.norm(r); u=np.cross(r,f)
    foc=1/math.tan(math.radians(14)); asp=W/H
    V=np.array([[t[0],t[1],t[2]] for t in tris for _ in (0,)]) if False else None
    zb=np.full((H,W),1e9); col=np.full((H,W,3),255,np.uint8); rid=np.zeros((H,W),np.int32)
    regs={}; light=np.array([-0.45,0.8,-0.4]); light/=np.linalg.norm(light)
    light=np.array([math.cos(az)*0.2-0.4, 0.8, 0.5*math.sin(az)-0.2]); light/=np.linalg.norm(light)
    P=lambda v:(lambda d:(( np.dot(d,r)*foc/asp)/np.dot(d,f), (np.dot(d,u)*foc)/np.dot(d,f), np.dot(d,f)))(np.array(v)-cam)
    for ti,(v0,v1,v2,c,reg) in enumerate(tris):
        n=normal(v0,v1,v2)
        cen=np.array(centroid(v0,v1,v2))
        if reg!='shadow' and np.dot(n,cam-cen)<=0: continue
        a,b,d=P(v0),P(v1),P(v2)
        if min(a[2],b[2],d[2])<=0.1: continue
        sx=[(p[0]*0.5+0.5)*W for p in (a,b,d)]; sy=[(0.5-p[1]*0.5)*H for p in (a,b,d)]
        x0=max(int(min(sx)),0); x1=min(int(max(sx))+1,W-1); y0=max(int(min(sy)),0); y1=min(int(max(sy))+1,H-1)
        if x0>x1 or y0>y1: continue
        gx,gy=np.meshgrid(np.arange(x0,x1+1)+0.5,np.arange(y0,y1+1)+0.5)
        den=(sy[1]-sy[2])*(sx[0]-sx[2])+(sx[2]-sx[1])*(sy[0]-sy[2])
        if abs(den)<1e-9: continue
        l0=((sy[1]-sy[2])*(gx-sx[2])+(sx[2]-sx[1])*(gy-sy[2]))/den
        l1=((sy[2]-sy[0])*(gx-sx[2])+(sx[0]-sx[2])*(gy-sy[2]))/den
        l2=1-l0-l1
        m=(l0>=-1e-4)&(l1>=-1e-4)&(l2>=-1e-4)
        if not m.any(): continue
        z=l0*a[2]+l1*b[2]+l2*d[2]
        sub=zb[y0:y1+1,x0:x1+1]
        bias = 0.0 if reg!='shadow' else 0.05
        ok=m&(z-bias<sub)
        if not ok.any(): continue
        sub[ok]=z[ok]-bias
        lam=max(0.0,float(np.dot(n if np.dot(n,cam-cen)>0 else -n,light)))
        shade=0.62 if lam<0.25 else (0.82 if lam<0.55 else 1.0)
        if reg in('glass',): shade=max(shade,0.8)
        cc=tuple(int(min(255,v*shade)) for v in c)
        if reg=='glass' and lam>0.55: cc=(98,116,138)
        col[y0:y1+1,x0:x1+1][ok]=cc
        if reg not in regs: regs[reg]=len(regs)+1
        rid[y0:y1+1,x0:x1+1][ok]=regs[reg]*1000+(0 if reg in('body','tire','sill','bump') else 0)
    # contorno: troca de regiao ou salto de profundidade
    zbd=np.where(zb>1e8,0,zb)
    edge=np.zeros((H,W),bool)
    dz=np.abs(np.diff(zbd,axis=1)); edge[:,1:]|=(dz>0.35)&(zbd[:,1:]>0)&(zbd[:,:-1]>0)
    dz=np.abs(np.diff(zbd,axis=0)); edge[1:,:]|=(dz>0.35)&(zbd[1:,:]>0)&(zbd[:-1,:]>0)
    edge[:,1:]|=(rid[:,1:]!=rid[:,:-1])&(rid[:,1:]>0)&(rid[:,:-1]>0)
    edge[1:,:]|=(rid[1:,:]!=rid[:-1,:])&(rid[1:,:]>0)&(rid[:-1,:]>0)
    bg=(zb>1e8); sil=np.zeros((H,W),bool)
    sil[:,1:]|=bg[:,1:]!=bg[:,:-1]; sil[1:,:]|=bg[1:,:]!=bg[:-1,:]
    shadowpix=(rid==regs.get('shadow',-1)*1000)
    sil&=~shadowpix
    col[(edge|sil)&~shadowpix]=(18,16,18)
    img=Image.fromarray(col).resize((W*scale,H*scale),Image.NEAREST)
    img.save(out)

if __name__=='__main__':
    az=float(sys.argv[1]); out=sys.argv[2]; el=float(sys.argv[3]) if len(sys.argv)>3 else 9.0
    render(az,out,el)
    print('ok',out,len(tris),'tris')
