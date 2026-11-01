"""Troca a roda de 5 raios da lateral pela roda bronze de 7 raios (oficial), desenhada em 2D pixel.
Mantem o aro bronze externo e o pneu originais; a imagem original nao e alterada (gera copia)."""
import math, sys
from PIL import Image, ImageDraw
SRC='/home/claude/jogo-corrida/arte/referencias/carro-honda-laranja/originais/lateral-direita.jpg'
BR=(170,110,58); BRH=(214,156,92); BRD=(104,64,34); OUT=(34,22,16); DK=(26,24,26); DISC=(58,56,58)
def roda(R=99, phase=0.0):
    k=4; S=2*R*k; im=Image.new('RGBA',(S,S),(0,0,0,0)); d=ImageDraw.Draw(im); c=S/2
    def circ(r,fill): d.ellipse((c-r*k,c-r*k,c+r*k,c+r*k),fill=fill)
    circ(R,BRD)                      # barril interno (sombra bronze)
    circ(R-9,BR)                     # parede do barril
    circ(R-17,DK)                    # fundo escuro
    circ(R*0.80,DISC); circ(R*0.62,DK)  # disco de freio
    for i in range(30):              # rebites no aro
        a=2*math.pi*i/30; rr=R-6
        x=c+rr*k*math.cos(a); y=c+rr*k*math.sin(a); d.ellipse((x-2.5*k/2*1.4,y-2.5*k/2*1.4,x+2.5*k/2*1.4,y+2.5*k/2*1.4),fill=(170,150,130))
    hub=R*0.22
    for i in range(7):               # raios
        a=phase+2*math.pi*i/7; ca,sa=math.cos(a),math.sin(a); pa,pb=-sa,ca
        r0=hub*0.8; r1=R-14; w0=R*0.105; w1=R*0.165
        def P(r,w): return (c+(r*ca+w*pa)*k, c+(r*sa+w*pb)*k)
        poly=[P(r0,-w0),P(r1,-w1),P(r1,w1),P(r0,w0)]
        d.polygon(poly,fill=OUT)
        s=1.0
        poly2=[P(r0+2,-w0+2.5),P(r1-1,-w1+3),P(r1-1,w1-3),P(r0+2,w0-2.5)]
        d.polygon(poly2,fill=BR)
        poly3=[P(r0+2,-w0+2.5),P(r1-1,-w1+3),P(r1-1,-w1+7),P(r0+2,-w0+6)]
        d.polygon(poly3,fill=BRH)
    circ(hub,OUT); circ(hub-2,BRD); circ(hub-4,BR)
    for i in range(5):               # parafusos do cubo
        a=phase+2*math.pi*i/5; x=c+hub*0.62*k*math.cos(a); y=c+hub*0.62*k*math.sin(a)
        d.ellipse((x-3*k,y-3*k,x+3*k,y+3*k),fill=OUT); d.ellipse((x-1.8*k,y-1.8*k,x+1.8*k,y+1.8*k),fill=(190,190,190))
    circ(hub*0.38,OUT); circ(hub*0.28,(90,90,95))
    # mascara circular + pixelizacao
    m=Image.new('L',(S,S),0); ImageDraw.Draw(m).ellipse((c-R*k,c-R*k,c+R*k,c+R*k),fill=255)
    im.putalpha(m)
    px=2.5
    small=im.resize((int(S/k/px),)*2,Image.NEAREST)
    return small.resize((2*R,2*R),Image.NEAREST)
def aplicar(img, centros, R=99):
    out=img.copy().convert('RGBA')
    for n,(cx,cy) in enumerate(centros):
        w=roda(R,phase=0.2+n*0.6); out.alpha_composite(w,(cx-R,cy-R))
    return out.convert('RGB')
if __name__=='__main__':
    L=Image.open(SRC).convert('RGB')
    res=aplicar(L,[(401,833),(1529,835)])
    res.save(sys.argv[1]); print('ok')
