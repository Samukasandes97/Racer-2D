"""Laterais: troca a roda de 9 raios pela bronze de 7 raios (copiada da referencia do Samuel) e
gera o lado esquerdo espelhando, mantendo os textos legiveis."""
import sys; sys.path.insert(0,'/home/claude/jogo-corrida/ferramentas/arte2d')
from roda_copia import face
from PIL import Image, ImageDraw, ImageOps
B='/home/claude/jogo-corrida/arte/carro-honda-laranja/'
base=Image.open(B+'oficiais/lateral-esquerda.jpg').convert('RGB')   # versao com tampa de combustivel
W=base.size[0]
out=base.copy()
for n,(cx,cy,R) in enumerate([(381,841,113),(1516,841,119)]):
    rf=R-10; rb=R-8
    mm=Image.new('L',(2*rb,2*rb),0); ImageDraw.Draw(mm).ellipse((0,0,2*rb-1,2*rb-1),fill=255)
    out.paste(Image.new('RGB',(2*rb,2*rb),(104,64,34)),(cx-rb,cy-rb),mm)
    f,m=face(2*rf,s0=-30,rot=n*20); out.paste(f,(cx-rf,cy-rf),m)
out.save(B+'ajustados/lateral-direita.png')
# lado esquerdo = espelho; textos re-colados sem espelhar
tx=[(1271,685,1322,748),(616,804,655,824),(1257,887,1286,910),(890,935,1047,961),(588,960,644,972)]
mir=ImageOps.mirror(out)
for (x0,y0,x1,y1) in tx:
    mir.paste(out.crop((x0,y0,x1,y1)),(W-x1,y0))
mir.save(B+'ajustados/lateral-esquerda.png')
for nm,im in (('d',out),('e',mir)):
    s=Image.new('RGB',(1200,360)); s.paste(im.crop((180,640,620,1010)).resize((440,370)),(0,0)); s.paste(im.crop((1330,640,1770,1010)).resize((440,370)),(450,0)); 
    s.save('/tmp/claude-0/-home-claude/3bd38bbe-1729-52b0-82d8-d24319b677a8/scratchpad/lat_%s.png'%nm)
print('ok')
