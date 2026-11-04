"""Prepara os sprites do carro para a demo de corrida (copias derivadas, originais intactos).
Recorta o carro, reduz para altura de 64px (estilo pixel-art da cena) e salva PNG."""
from PIL import Image
import numpy as np
SRC = '/home/claude/jogo-corrida/demos/giro-camera/img/'
OUT = '/home/claude/jogo-corrida/demos/corrida-shibuya/img/'
# reta = traseira; virando p/ direita vemos o lado esquerdo (315/337.5); virando p/ esquerda o lado direito (45/22.5)
M = {'c': 'car_000', 'r1': 'p_3375', 'r2': 'car_315', 'l1': 'p_0225', 'l2': 'car_045'}
H = 64
for k, f in M.items():
    im = Image.open(SRC + f + '.webp').convert('RGBA')
    bb = im.getchannel('A').point(lambda v: 255 if v > 40 else 0).getbbox()
    im = im.crop(bb)
    s = H / im.size[1]
    im = im.resize((max(1, round(im.size[0] * s)), H), Image.LANCZOS)
    im.save(OUT + 'car_%s.png' % k)
    print(k, im.size)
