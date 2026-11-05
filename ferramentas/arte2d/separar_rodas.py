"""Separa as rodas do carro (copias derivadas; originais intactos).
Para cada vista oficial gera: corpo com buraco no lugar da roda, 'poco' escuro, e uma imagem por roda (pneu+roda).
Tambem gera o disco da roda 'desentortado' (elipse->circulo) para girar em tempo real."""
import json, sys, numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
import colorsys
B = '/home/claude/jogo-corrida/arte/carro-honda-laranja/sprites/png/'
OUT = '/home/claude/jogo-corrida/arte/carro-honda-laranja/rig-hires/'   # pecas em alta resolucao (arte)
GAME = '/home/claude/jogo-corrida/demos/corrida-shibuya/img/rig/'       # pecas na escala do jogo (carro com 64 px de altura)
SC = 0.1
import os; os.makedirs(OUT, exist_ok=True); os.makedirs(GAME, exist_ok=True)
# vistas: arquivo, rodas [(nome, cx, cy, rx, ry, rot_graus, face(cx,cy,a,b,tilt) ou None)]  (coordenadas no recorte do carro)
V = {
 'c':  ('car_000_traseira', [('rl', 62, 500, 56, 135, 0, None), ('rr', 898, 500, 58, 135, 0, None)]),
 'l2': ('car_045_traseira-3-4-direita', [('r', 785, 490, 128, 156, -4, (815, 482, 60, 122, -4)), ('f', 1275, 428, 98, 122, -4, (1280, 420, 52, 108, -3))]),
 'r2': ('car_315_traseira-3-4-esquerda', [('r', 715, 490, 128, 152, 3, (672, 482, 74, 122, 3)), ('f', 125, 435, 96, 122, 3, (98, 425, 52, 106, 2))]),
}
def is_body(rgb):
    r, g, b = [c / 255 for c in rgb]; h, s, v = colorsys.rgb_to_hsv(r, g, b)
    return (0.02 <= h <= 0.12) and s > .55 and v > .5
def run(key, fn, wheels, show=False):
    im = Image.open(B + fn + '.png').convert('RGBA'); bb = im.getbbox(); im = im.crop(bb)
    a = np.asarray(im).copy(); H, W = a.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W]
    hole = np.zeros((H, W), bool); info = []
    for (nm, cx, cy, rx, ry, rot, face) in wheels:
        t = np.deg2rad(rot); dx, dy = xx - cx, yy - cy
        u = dx * np.cos(t) + dy * np.sin(t); v = -dx * np.sin(t) + dy * np.cos(t)
        ell = (u / rx) ** 2 + (v / ry) ** 2 <= 1
        hsv = np.zeros((H, W), bool)
        if key=='c':
            ell &= ~(((xx>=76)&(xx<=135)|(xx>=830)&(xx<=888))&(yy>=395)&(yy<=512))
        sub = ell & (a[:, :, 3] > 40)
        ys, xs = np.where(sub)
        rgb = a[ys, xs, :3]
        body = np.array([is_body(c) for c in rgb])
        m = np.zeros((H, W), bool); m[ys[~body], xs[~body]] = True
        m = ndimage.binary_opening(m, iterations=2); m = ndimage.binary_closing(m, iterations=3)
        lab, n = ndimage.label(m)
        if n > 1:
            sz = ndimage.sum(m, lab, range(1, n + 1)); m = lab == (1 + int(np.argmax(sz)))
        m = ndimage.binary_fill_holes(m)
        hole |= m
        x0, y0, x1, y1 = [int(v) for v in (np.where(m)[1].min(), np.where(m)[0].min(), np.where(m)[1].max() + 1, np.where(m)[0].max() + 1)]
        w = a.copy(); w[~m] = 0; Image.fromarray(w[y0:y1, x0:x1]).save(OUT + '%s_wheel_%s.png' % (key, nm))
        d = dict(nome=nm, x=x0, y=y0, w=x1 - x0, h=y1 - y0, cx=cx, cy=cy)
        if face:
            fx, fy, fa, fb, ft = face; r = fb
            # desentorta o disco: elipse (a,b,tilt) -> circulo de raio b
            S = 2 * r + 2; circ = Image.new('RGBA', (S, S), (0, 0, 0, 0))
            src = Image.fromarray(a); tt = np.deg2rad(ft)
            # mapeia cada pixel do circulo para a imagem
            gy, gx = np.mgrid[0:S, 0:S]; ux = (gx - S / 2) * (fa / fb); uy = (gy - S / 2)
            sx = fx + ux * np.cos(tt) - uy * np.sin(tt); sy = fy + ux * np.sin(tt) + uy * np.cos(tt)
            ix = np.clip(np.round(sx).astype(int), 0, W - 1); iy = np.clip(np.round(sy).astype(int), 0, H - 1)
            out = a[iy, ix].copy(); inside = ((gx - S / 2) ** 2 + (gy - S / 2) ** 2) <= r * r
            out[~inside] = 0; Image.fromarray(out).save(OUT + '%s_face_%s.png' % (key, nm))
            d['face'] = dict(cx=fx, cy=fy, a=fa, b=fb, tilt=ft, r=r)
        info.append(d)
    body = a.copy(); body[hole] = 0
    Image.fromarray(body).save(OUT + '%s_body.png' % key)
    well = np.zeros_like(a); well[ndimage.binary_dilation(hole, iterations=3) & (a[:, :, 3] > 0) | hole] = (14, 12, 20, 255)
    Image.fromarray(well).save(OUT + '%s_well.png' % key)
    # visual de conferencia
    chk = Image.new('RGB', (W, H), (205, 205, 210)); chk.paste(Image.fromarray(body), (0, 0), Image.fromarray(body))
    ov = np.asarray(chk).copy(); ov[hole] = (255, 0, 255); Image.fromarray(ov).save('/tmp/claude-0/-home-claude/3bd38bbe-1729-52b0-82d8-d24319b677a8/scratchpad/chk_%s.png' % key)
    return dict(w=W, h=H, rodas=info)
def escala(meta):
    g = {}
    for k, m in meta.items():
        rodas = []
        for r in m['rodas']:
            d = dict(nome=r['nome'], x=round(r['x'] * SC), y=round(r['y'] * SC))
            im = Image.open(OUT + '%s_wheel_%s.png' % (k, r['nome'])); im = im.resize((max(1, round(im.size[0] * SC)), max(1, round(im.size[1] * SC))), Image.LANCZOS)
            im.save(GAME + '%s_wheel_%s.png' % (k, r['nome'])); d['w'], d['h'] = im.size
            if 'face' in r:
                f = r['face']; fi = Image.open(OUT + '%s_face_%s.png' % (k, r['nome'])); S2 = max(2, round(fi.size[0] * SC))
                fi.resize((S2, S2), Image.LANCZOS).save(GAME + '%s_face_%s.png' % (k, r['nome']))
                d['face'] = dict(cx=round(f['cx'] * SC, 2), cy=round(f['cy'] * SC, 2), a=round(f['a'] * SC, 2), b=round(f['b'] * SC, 2), tilt=f['tilt'], S=S2)
            rodas.append(d)
        for part in ('body', 'well'):
            im = Image.open(OUT + '%s_%s.png' % (k, part)); im = im.resize((round(im.size[0] * SC), round(im.size[1] * SC)), Image.LANCZOS); im.save(GAME + '%s_%s.png' % (k, part))
        g[k] = dict(w=round(m['w'] * SC), h=round(m['h'] * SC), rodas=rodas)
    json.dump(g, open(GAME + 'rig.json', 'w'), indent=1)
    return g

if __name__ == '__main__':
    meta = {}
    for k, (fn, wh) in V.items():
        if wh: meta[k] = run(k, fn, wh)
    json.dump(meta, open(OUT + 'rig.json', 'w'), indent=1)
    print(json.dumps(escala(meta)))
