"""Copia a roda bronze de 7 raios da traseira 3/4 e a transforma em vista frontal (lateral do carro).
Usa o lado melhor resolvido da roda (direita do cubo) e repete o setor 7 vezes (simetria da roda)."""
from PIL import Image, ImageDraw, ImageFilter
import math, numpy as np
O='/home/claude/jogo-corrida/arte/referencias/carro-honda-laranja/originais/'
T=Image.open(O+'traseira-3-4-direita.jpg').convert('RGB')
L=Image.open(O+'lateral-direita.jpg').convert('RGB')
CX,CY,A,B=1130,926,50,126      # elipse do aro (anel de rebites)
HUBX,HUBY=1098,926
SRC=np.asarray(T.filter(ImageFilter.BoxBlur(1)))
OUT=(34,22,16); SIL=(150,150,155)
def face(diam, s0=0.0, rot=0.0, k=2.5):
    n=int(round(diam/k)); n=n if n%2==0 else n+1
    ys,xs=np.mgrid[0:n,0:n]; u=(xs+0.5)/n*2-1; v=(ys+0.5)/n*2-1
    rho=np.sqrt(u*u+v*v); phi=np.arctan2(v,u)-math.radians(rot)
    sec=2*math.pi/7
    d=((phi+sec/2)%sec)-sec/2
    t=math.radians(s0)+d
    rx=CX+A*np.cos(t); ry=CY+B*np.sin(t)
    sx=HUBX+rho*(rx-HUBX); sy=HUBY+rho*(ry-HUBY)
    sx=np.clip(np.round(sx).astype(int),0,T.size[0]-1); sy=np.clip(np.round(sy).astype(int),0,T.size[1]-1)
    img=Image.fromarray(SRC[sy,sx])
    # cubo desenhado (5 parafusos), por cima
    dr=ImageDraw.Draw(img); c=n/2; hr=n*0.085
    dr.ellipse((c-hr,c-hr,c+hr,c+hr),fill=(40,32,28))
    for i in range(5):
        a=math.radians(rot)+2*math.pi*i/5; x=c+hr*0.62*math.cos(a); y=c+hr*0.62*math.sin(a); r=n*0.013
        dr.ellipse((x-r,y-r,x+r,y+r),fill=(150,150,155))
    r=n*0.022; dr.ellipse((c-r,c-r,c+r,c+r),fill=(90,90,96))
    img=img.resize((diam,diam),Image.NEAREST)
    m=Image.new('L',(n,n),0); ImageDraw.Draw(m).ellipse((0,0,n-1,n-1),fill=255)
    return img,m.resize((diam,diam),Image.NEAREST)
def aplicar(img,centros,R=99,r_face=95,s0=0.0):
    out=img.copy()
    for n,(cx,cy) in enumerate(centros):
        base=Image.new('RGB',(2*R,2*R),(104,64,34)); mm=Image.new('L',(2*R,2*R),0); ImageDraw.Draw(mm).ellipse((0,0,2*R-1,2*R-1),fill=255)
        out.paste(base,(cx-R,cy-R),mm)
        f,m=face(2*r_face,s0=s0,rot=n*20); out.paste(f,(cx-r_face,cy-r_face),m)
    return out
if __name__=='__main__':
    import sys
    sheet=Image.new('RGB',(1500,500),'white')
    for i,s0 in enumerate([-30,-15,0,15,30]):
        r=aplicar(L,[(401,833)],s0=s0); sheet.paste(r.crop((301,733,501,933)).resize((300,300),Image.NEAREST),(i*300,0))
    sheet.save(sys.argv[1])
