"""Gera as camadas HD do carro (derivadas de arte/carro-honda-laranja/rig-hires; originais NAO sao alterados):
 - vidros semitransparentes (mascara por cor, so na regiao das janelas)
 - tinta mais viva + brilho de verniz (faixa de reflexo no ombro, reflexo do ceu no teto/capo, ponto de luz)
 - tudo reduzido para escala HS=.3 (carro ~600 px de largura) e meta ajustado."""
import json,os,sys,numpy as np
from PIL import Image
from scipy import ndimage as nd
SRC='/home/claude/jogo-corrida/arte/carro-honda-laranja/rig-hires/';DST='/home/claude/jogo-corrida/demos/mundo-aberto/img/rig-hd/';HS=.3
os.makedirs(DST,exist_ok=True);meta=json.load(open(SRC+'rig.json'))
def rgb2hsv(a):
    return np.array(Image.fromarray(a,'RGB').convert('HSV')).astype(float)
def process(k,im):
    a=np.array(im).astype(float);h,w=a.shape[:2];rgb=a[...,:3];al=a[...,3]
    r,g,b=rgb[...,0],rgb[...,1],rgb[...,2];mx=rgb.max(2);mn=rgb.min(2);lum=.3*r+.59*g+.11*b
    paint=(al>200)&(r>g*1.12)&(r-b>45)
    yy,xx=np.mgrid[0:h,0:w]
    reg=(yy<h*(.36 if k=='c' else .47))&((xx>w*.14)&(xx<w*.86) if k=='c' else True)
    cand=(al>200)&~paint&(mx-mn<70)&(lum>28)&(lum<200)&reg
    cand=nd.binary_closing(cand,iterations=2)&(al>200)&~paint
    lab,n=nd.label(cand)
    if n:
        sz=nd.sum(cand,lab,range(1,n+1));keep=np.isin(lab,[i+1 for i,s in enumerate(sz) if s>h*h*.004]);cand=keep
    glass=nd.binary_erosion(cand,iterations=2)   # deixa moldura/contorno opacos
    glass=nd.gaussian_filter(glass.astype(float),2.0)
    # tinta viva: satura e clareia levemente
    pm=nd.gaussian_filter(paint.astype(float),1.2)
    hsv=rgb2hsv(np.clip(rgb,0,255).astype(np.uint8));hsv[...,1]=np.clip(hsv[...,1]*1.22,0,255);hsv[...,2]=np.clip(hsv[...,2]*1.08+6,0,255)
    viv=np.array(Image.fromarray(hsv.astype(np.uint8),'HSV').convert('RGB')).astype(float)
    out=rgb*(1-pm[...,None])+viv*pm[...,None]
    # verniz: reflexo do ceu (degrade claro-azulado no alto de cada regiao de tinta) + faixa de brilho no ombro
    top=np.zeros((h,w));
    cs=np.cumsum(paint,0);first=np.argmax(paint,0)  # primeira linha de tinta por coluna
    dist=(yy-first[None,:]).clip(0,None).astype(float)
    sky=np.exp(-dist/(h*.07))*paint
    out+= (np.array([255,240,215])-out)*(sky[...,None]*.34*pm[...,None])
    band=np.exp(-((yy-h*(.50 if k!='c' else .52)-(xx-w*.5)*.06)/(h*.022))**2)*paint
    out+= (255-out)*(band[...,None]*.30)
    gx,gy=(w*(.32 if k!='r3' else .62)),h*.40
    spot=np.exp(-(((xx-gx)/(w*.07))**2+((yy-gy)/(h*.05))**2))*paint
    out+= (255-out)*(spot[...,None]*.45)
    # vidro: reflexo diagonal claro + transparencia
    diag=np.clip(np.sin((xx+yy*1.2)/(w*.05))*.5+.5,0,1)**6
    gl=glass[...,None];out=out+(np.array([190,225,255])-out)*gl*(.10+.22*diag[...,None])
    alpha=al*(1-glass*.50)
    o=np.dstack([np.clip(out,0,255),alpha]).astype(np.uint8)
    return Image.fromarray(o,'RGBA')
def save(im,name):
    im=im.resize((max(1,round(im.width*HS)),max(1,round(im.height*HS))),Image.LANCZOS);im.save(DST+name,optimize=True)
M={}
for k,m in meta.items():
    save(process(k,Image.open(SRC+k+'_body.png').convert('RGBA')),k+'_body.png')
    save(Image.open(SRC+k+'_well.png').convert('RGBA'),k+'_well.png')
    mm={'w':round(m['w']*HS),'h':round(m['h']*HS),'rodas':[]}
    for r in m['rodas']:
        save(Image.open(SRC+'%s_wheel_%s.png'%(k,r['nome'])).convert('RGBA'),'%s_wheel_%s.png'%(k,r['nome']))
        q={'nome':r['nome'],**{n:r[n]*HS for n in('x','y','w','h','cx','cy')}}
        if 'face' in r:
            f=r['face'];fi=Image.open(SRC+'%s_face_%s.png'%(k,r['nome'])).convert('RGBA');save(fi,'%s_face_%s.png'%(k,r['nome']))
            q['face']={'cx':f['cx']*HS,'cy':f['cy']*HS,'a':f['a'],'b':f['b'],'tilt':f['tilt'],'S':round(fi.width*HS)}
        mm['rodas'].append(q)
    M[k]=mm
json.dump(M,open(DST+'rig.json','w'),indent=1);print('ok',sorted(os.listdir(DST))[:3],len(os.listdir(DST)))
