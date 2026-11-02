"""Prototipo: converte uma pose do video (render realista) para o estilo pixel-art com contorno.
Recorta o fundo, achata o sombreado, reduz as cores, pixeliza e desenha o contorno preto."""
import sys, numpy as np, cv2
from PIL import Image
BLOCO=3            # tamanho do pixel final (px) nos sprites de 640 de altura
ALTURA=640
def recorta(bgr):
    h,w=bgr.shape[:2]; mask=np.full((h,w),cv2.GC_PR_BGD,np.uint8)
    # chute inicial: o carro e laranja saturado ou escuro; fundo e cinza claro
    hsv=cv2.cvtColor(bgr,cv2.COLOR_BGR2HSV); s=hsv[:,:,1]; v=hsv[:,:,2]
    mask[(s>110)]=cv2.GC_PR_FGD; mask[(s>170)&(v>120)]=cv2.GC_FGD
    mask[(v<70)]=cv2.GC_PR_FGD
    mask[:int(h*0.04)]=cv2.GC_BGD; mask[-int(h*0.03):]=cv2.GC_BGD; mask[:,:int(w*0.02)]=cv2.GC_BGD; mask[:,-int(w*0.02):]=cv2.GC_BGD
    bg=np.zeros((1,65),np.float64); fg=np.zeros((1,65),np.float64)
    cv2.grabCut(bgr,mask,None,bg,fg,4,cv2.GC_INIT_WITH_MASK)
    m=((mask==cv2.GC_FGD)|(mask==cv2.GC_PR_FGD)).astype(np.uint8)
    n,lab,st,_=cv2.connectedComponentsWithStats(m); 
    if n>1:
        k=1+np.argmax(st[1:,cv2.CC_STAT_AREA]); m=(lab==k).astype(np.uint8)
    m=cv2.morphologyEx(m,cv2.MORPH_CLOSE,np.ones((9,9),np.uint8)); 
    # preenche buracos
    ff=m.copy(); cv2.floodFill(ff,np.zeros((h+2,w+2),np.uint8),(0,0),2); m=(ff!=2).astype(np.uint8)
    return m
def pixelizar(path,saida,cores=26):
    bgr=cv2.imread(path); m=recorta(bgr)
    ys,xs=np.where(m>0); x0,x1,y0,y1=xs.min(),xs.max()+1,ys.min(),ys.max()+1
    bgr=bgr[y0:y1,x0:x1]; m=m[y0:y1,x0:x1]
    gh=ALTURA//BLOCO; gw=max(8,round(bgr.shape[1]*gh/bgr.shape[0]))
    sm=cv2.bilateralFilter(bgr,9,40,9); sm=cv2.bilateralFilter(sm,9,40,9)
    small=cv2.resize(sm,(gw,gh),interpolation=cv2.INTER_AREA); ms=cv2.resize(m,(gw,gh),interpolation=cv2.INTER_AREA)>0.5
    lab=cv2.cvtColor(small,cv2.COLOR_BGR2LAB).reshape(-1,3).astype(np.float32)
    sel=ms.reshape(-1)
    crit=(cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER,30,0.5)
    _,lbl,cen=cv2.kmeans(lab[sel],cores,None,crit,3,cv2.KMEANS_PP_CENTERS)
    q=np.zeros_like(lab); q[sel]=cen[lbl.reshape(-1)]; idx=np.full(len(lab),-1); idx[sel]=lbl.reshape(-1)
    q=q.reshape(gh,gw,3).astype(np.uint8); idx=idx.reshape(gh,gw)
    rgb=cv2.cvtColor(q,cv2.COLOR_LAB2RGB)
    rgb=cv2.medianBlur(rgb,3)                      # tira pixels soltos
    # apaga letreiro branco do para-brisa (parte de cima do carro)
    gg=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY); chroma=rgb.max(axis=2).astype(int)-rgb.min(axis=2)
    ban=((gg>190)&(chroma<35)&ms); ban[int(gh*0.30):]=False
    ban=cv2.dilate(ban.astype(np.uint8),np.ones((3,3),np.uint8))
    if ban.sum()>0: rgb=cv2.inpaint(rgb,ban,3,cv2.INPAINT_TELEA)
    # contorno: silhueta + troca forte de regiao
    edge=np.zeros((gh,gw),bool)
    sil=np.zeros((gh,gw),bool); sil[:,1:]|=ms[:,1:]!=ms[:,:-1]; sil[1:,:]|=ms[1:,:]!=ms[:-1,:]
    g=cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY).astype(int)
    dx=np.abs(np.diff(g,axis=1))>38; dy=np.abs(np.diff(g,axis=0))>38
    edge[:,1:]|=dx&ms[:,1:]&ms[:,:-1]; edge[1:,:]|=dy&ms[1:,:]&ms[:-1,:]
    out=rgb.copy(); out[(edge|sil)]=(20,18,20)
    rgba=np.dstack([out,(ms*255).astype(np.uint8)])
    im=Image.fromarray(rgba,'RGBA').resize((gw*BLOCO,gh*BLOCO),Image.NEAREST); im.save(saida); return im
if __name__=='__main__':
    pixelizar(sys.argv[1],sys.argv[2])
