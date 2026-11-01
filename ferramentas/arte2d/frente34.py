"""Frente 3/4 em 2D: junta a imagem de FRENTE com a LATERAL (ja com roda bronze), cada uma achatada
pelo angulo de visao, com perspectiva leve. Nenhuma imagem original e alterada."""
import numpy as np, math, sys
from PIL import Image, ImageChops, ImageOps
O='/home/claude/jogo-corrida/arte/referencias/carro-honda-laranja/originais/'
G='/home/claude/jogo-corrida/arte/carro-honda-laranja/gerados/'
def homog(src,dst):
    A=[];b=[]
    for (x,y),(u,v) in zip(dst,src):   # dst->src
        A.append([x,y,1,0,0,0,-u*x,-u*y]); b.append(u)
        A.append([0,0,0,x,y,1,-v*x,-v*y]); b.append(v)
    return np.linalg.solve(np.array(A,float),np.array(b,float))
def warp(img,dst,size):
    w,h=img.size; src=[(0,0),(w,0),(w,h),(0,h)]
    return img.transform(size,Image.PERSPECTIVE,tuple(homog(src,dst)),Image.NEAREST,fillcolor=(255,255,255))
def crop_car(im,thr=200):
    a=np.asarray(im.convert('L')); ys,xs=np.where(a<thr); return im.crop((xs.min(),ys.min(),xs.max()+1,ys.max()+1))
def gerar(alpha_deg=40, s_side=0.90, s_front=0.93, out=None):
    side=crop_car(Image.open(G+'lateral-direita_roda-bronze-7raios.png').convert('RGB'))
    fr=crop_car(Image.open(O+'frente.jpg').convert('RGB'))
    H=side.size[1]; fr=fr.resize((int(fr.size[0]*H/fr.size[1]),H),Image.LANCZOS)
    al=math.radians(alpha_deg); ws=int(side.size[0]*math.sin(al)); wf=int(fr.size[0]*math.cos(al))
    W,Hc=2600,1200; xj=100+ws; yg=1000; yr=yg-H; yh=yg-0.45*H
    far=lambda y,s: yh+(y-yh)*s
    dside=[(xj-ws,far(yr,s_side)),(xj,yr),(xj,yg),(xj-ws,far(yg,s_side))]
    dfr=[(xj,yr),(xj+wf,far(yr,s_front)),(xj+wf,far(yg,s_front)),(xj,yg)]
    a=warp(side,dside,(W,Hc)); b=warp(fr,dfr,(W,Hc))
    comp=ImageChops.darker(a,b)
    comp=crop_car(comp,thr=235); pad=40
    canvas=Image.new('RGB',(comp.size[0]+2*pad,comp.size[1]+2*pad),(255,255,255)); canvas.paste(comp,(pad,pad))
    if out: canvas.save(out)
    return canvas
if __name__=='__main__':
    c=gerar(float(sys.argv[2]) if len(sys.argv)>2 else 40,out=sys.argv[1]); print(c.size)
