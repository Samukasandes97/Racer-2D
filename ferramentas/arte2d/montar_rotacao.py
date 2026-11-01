"""Monta as 8 direcoes do carro para a camera de tras girar 360 graus.
az 0 = camera atras do carro; a camera anda para o lado DIREITO do carro (sentido horario visto de cima).
Nao altera nenhuma imagem de origem: le e gera copias novas em sprites/."""
import json, os
import numpy as np
from PIL import Image
from scipy import ndimage

B = '/home/claude/jogo-corrida/arte/carro-honda-laranja/'
R = '/home/claude/jogo-corrida/arte/referencias/carro-honda-laranja/originais/'
OUT = '/home/claude/jogo-corrida/arte/carro-honda-laranja/sprites/'
os.makedirs(OUT + 'png', exist_ok=True)

DIRS = [  # (azimute, nome, arquivo)
    (0,   'traseira',            R + 'traseira.jpg'),
    (45,  'traseira-3-4-direita', B + 'ajustados/traseira-3-4-direita.jpg'),
    (90,  'lateral-direita',     B + 'ajustados/lateral-direita.png'),
    (135, 'frente-3-4-direita',  B + 'ajustados/frente-3-4-direita.png'),
    (180, 'frente',              R + 'frente.jpg'),
    (225, 'frente-3-4-esquerda', B + 'ajustados/frente-3-4-esquerda.png'),
    (270, 'lateral-esquerda',    B + 'ajustados/lateral-esquerda.png'),
    (315, 'traseira-3-4-esquerda', B + 'ajustados/traseira-3-4-esquerda.jpg'),
]
CW, CH = 2100, 800          # tela de cada sprite
CAR_H = 640                 # altura do carro (roda ao teto) em px
GROUND = 735                # linha do chao (base do carro)

def recorta_fundo(im):
    a = np.asarray(im.convert('RGB')).astype(int)
    mn = a.min(axis=2)
    cand = mn >= 232                                   # quase branco
    lab, n = ndimage.label(cand)
    borda = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bg = np.isin(lab, list(borda))
    # suaviza a borda de 1px
    alpha = (~bg).astype(float)
    alpha = ndimage.gaussian_filter(alpha, 0.7)
    alpha = np.clip((alpha - 0.35) / 0.4, 0, 1)
    rgba = np.dstack([a.astype('uint8'), (alpha * 255).astype('uint8')])
    return Image.fromarray(rgba, 'RGBA')

def maior_bbox(img):
    al = np.asarray(img)[:, :, 3] > 40
    lab, n = ndimage.label(al)
    if n == 0: return img.getbbox()
    sizes = ndimage.sum(al, lab, range(1, n + 1))
    keep = np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s > 0.02 * sizes.max()])
    ys, xs = np.where(keep)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1

manifesto = {'camera': 'atras do carro (az 0), girando para o lado direito do carro', 'canvas': [CW, CH],
             'chao_y': GROUND, 'direcoes': []}
for az, nome, f in DIRS:
    im = recorta_fundo(Image.open(f))
    x0, y0, x1, y1 = maior_bbox(im)
    im = im.crop((x0, y0, x1, y1))
    s = CAR_H / im.size[1]
    im = im.resize((max(1, round(im.size[0] * s)), CAR_H), Image.LANCZOS)
    tela = Image.new('RGBA', (CW, CH), (0, 0, 0, 0))
    tela.alpha_composite(im, ((CW - im.size[0]) // 2, GROUND - CAR_H))
    tela.save(OUT + 'png/car_%03d_%s.png' % (az, nome))
    manifesto['direcoes'].append({'azimute': az, 'nome': nome, 'arquivo': 'png/car_%03d_%s.png' % (az, nome),
                                  'origem': os.path.relpath(f, '/home/claude/jogo-corrida')})
json.dump(manifesto, open(OUT + 'manifesto.json', 'w'), ensure_ascii=False, indent=2)

# folha de contato + spritesheet (8 colunas)
sheet = Image.new('RGBA', (CW * 8, CH), (0, 0, 0, 0))
for i, d in enumerate(manifesto['direcoes']):
    sheet.alpha_composite(Image.open(OUT + d['arquivo']), (i * CW, 0))
sheet.save(OUT + 'spritesheet_8dir.png')
prev = Image.new("RGB", (CW * 4 // 3, CH * 2 // 3), (190, 190, 196))
for i, d in enumerate(manifesto['direcoes']):
    t = Image.open(OUT + d['arquivo']).resize((CW // 3, CH // 3), Image.LANCZOS)
    prev.paste(t, ((i % 4) * CW // 3, (i // 4) * CH // 3), t)
prev.save('/tmp/claude-0/-home-claude/3bd38bbe-1729-52b0-82d8-d24319b677a8/scratchpad/contato8.png')
print('ok')
