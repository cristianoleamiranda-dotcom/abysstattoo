#!/usr/bin/env python3
"""
Abyss Story UBICACIÓN — 1080x1920 · ≤15 s · 30 fps · sin audio.
Estructura: aerial dron (descenso + pin drop) → fachada noche → fachada día →
vitrina → whip a card "HORAS DISPONIBLES".
Motion: ease-out-back en héroes, ease-out-cubic en filas, ease-in quad de salida,
zoom punch alternado, xfade motivadas (fade/slideup/circleopen/slideleft-whip).
"""
import os, sys, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()

W, H = 1080, 1920
CARBON = (41, 37, 33); CREMA = (234, 227, 221); CREMA2 = (198, 183, 171)
CREMA3 = (143, 127, 115); TEAL = (79, 122, 114); TEAL_L = (158, 196, 186)
LOGO = 'assets/logo_abyss_256.png'
OUT = 'material/stories/ubicacion'
OV = f'{OUT}/overlays'

_cin = ImageFont.truetype('/tmp/cinzel.ttf', 100)
_mon = ImageFont.truetype('/tmp/montserrat.ttf', 100)
def cin(s): return ImageFont.truetype('/tmp/cinzel.ttf', int(s))
def mon(s): return ImageFont.truetype('/tmp/montserrat.ttf', int(s))

def tracked_width(d, text, f, tr):
    return d.textlength(text, font=f) + tr*(len(text)-1)
def draw_tracked(d, cx, y, text, f, tr, fill):
    w = tracked_width(d, text, f, tr)
    d.text((cx-w/2, y), text, font=f, fill=fill+(255,), spacing=0,
           features=None) if False else d.text((cx-w/2, y), text, font=f, fill=fill+(255,))
    # tracking manual: dibujar char a char
def draw_tracked(d, cx, y, text, f, tr, fill):
    w = tracked_width(d, text, f, tr)
    x = cx - w/2
    for ch in text:
        d.text((x, y), ch, font=f, fill=fill+(255,))
        x += d.textlength(ch, font=f) + tr
def fit_size(text, base, tr, maxw, fam):
    s = base
    while s > 30:
        f = cin(s) if fam == cin else mon(s)
        if tracked_width(ImageDraw.Draw(Image.new('RGB', (8, 8))), text, f, int(s*tr)) <= maxw:
            return s
        s -= 4
    return s
def diamond(d, cx, cy, r, fill):
    d.polygon([(cx, cy-r), (cx+r, cy), (cx, cy+r), (cx-r, cy)], fill=fill)
def separator(d, y):
    d.line([W//2-190, y, W//2-26, y], fill=CREMA2+(140,), width=1)
    d.line([W//2+26, y, W//2+190, y], fill=CREMA2+(140,), width=1)
    diamond(d, W//2, y, 6, TEAL_L+(255,))

def new_layer():
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)

# ---------- grade de marca (sat .88 · S-curve 1.06 · sombras +10 · luces -6) ----------
def grade(im):
    im = ImageEnhance.Color(im).enhance(0.88)
    lut = []
    for v in range(256):
        x = v/255
        x = min(max((x-0.5)*1.06+0.5, 0), 1)
        x = x + 0.10*(1-x)**2 - 0.06*x**3
        lut.append(min(max(int(x*255), 0), 255))
    return im.point(lut*3)

# ---------- timing ----------
DS = [3.6, 3.0, 3.0, 2.9]; TR_ = [0.30, 0.32, 0.38, 0.28]
O1 = DS[0]-TR_[0]            # 3.30
O2 = O1+DS[1]-TR_[1]         # 5.98
O3 = O2+DS[2]-TR_[2]         # 8.60
O4 = O3+DS[3]-TR_[3]         # 11.22
TOTAL = O4+3.4               # 14.62
T_EXIT = 10.9

def P(st, d): return f"min(max((t-{st})/{d},0),1)"
def back(p): return f"(-2.70158*pow({p}-1,3)-1.70158*pow({p}-1,2))"
def cubic(p): return f"pow(1-{p},3)"
def quadin(p): return f"pow({p},2)"

# ---------- overlays ----------
def ov_aerial():
    """eyebrow + H1 + pin + label de calle"""
    els = {}
    im, d = new_layer()
    draw_tracked(d, W//2, 300, 'ABYSS TATTOO STUDIO · SAN BERNARDO', mon(27), 9, CREMA2)
    els['eyebrow'] = im
    im, d = new_layer()
    s = fit_size('NOS ENCONTRÁS', 110, .12, 920, cin)
    draw_tracked(d, W//2, 372, 'NOS ENCONTRÁS', cin(s), int(s*.12), CREMA)
    els['h1a'] = im
    im, d = new_layer()
    s = fit_size('EN SAN BERNARDO', 110, .12, 920, cin)
    draw_tracked(d, W//2, 372+int(s*1.12), 'EN SAN BERNARDO', cin(s), int(s*.12), CREMA)
    els['h1b'] = im
    im, d = new_layer()   # pin: diamante teal + anillo
    cx, cy = W//2, 1180
    d.ellipse([cx-150, cy-150, cx+150, cy+150], outline=TEAL_L+(200,), width=3)
    d.ellipse([cx-96, cy-96, cx+96, cy+96], outline=TEAL_L+(120,), width=2)
    diamond(d, cx, cy, 34, TEAL_L+(255,))
    diamond(d, cx, cy, 14, CARBON+(255,))
    els['pin'] = im
    im, d = new_layer()   # pulso exterior
    d.ellipse([W//2-210, 1180-210, W//2+210, 1180+210], outline=TEAL_L+(110,), width=2)
    els['pulse'] = im
    im, d = new_layer()   # chip de calle
    txt = 'JOSÉ JOAQUÍN PÉREZ 528'
    f = mon(30); tr = 4
    tw = tracked_width(d, txt, f, tr)
    pw, ph = tw+110, 84
    x0, y0 = (W-pw)//2, 1360-ph//2
    d.rounded_rectangle([x0, y0, x0+pw, y0+ph], radius=ph//2, fill=CARBON+(225,), outline=TEAL_L+(255,), width=2)
    draw_tracked(d, W//2, y0+24, txt, f, tr, CREMA)
    els['chip'] = im
    return els

def ov_shots():
    els = {}
    im, d = new_layer()
    draw_tracked(d, W//2, 1560, 'VISTA AÉREA · BARRIO DEL ESTUDIO', mon(26), 4, CREMA3)
    els['cap_aerial'] = im
    im, d = new_layer()
    draw_tracked(d, W//2, 1560, 'FACHADA Y MURAL · ABYSS TATTOO', mon(26), 4, CREMA3)
    els['cap_night'] = im
    im, d = new_layer()
    draw_tracked(d, W//2, 1560, 'TERRAZA DE ESPERA · JOSÉ JOAQUÍN PÉREZ 528', mon(26), 4, CREMA3)
    els['cap_day'] = im
    im, d = new_layer()
    draw_tracked(d, W//2, 1560, 'DESDE 2009 · TATUAJE Y PIERCING PROFESIONAL', mon(26), 4, CREMA3)
    els['cap_vitrina'] = im
    return els

def ov_card():
    els = {}
    im, d = new_layer()
    d.rectangle([54, 54, W-55, H-55], outline=CREMA2+(255,), width=2)
    d.rectangle([66, 66, W-67, H-67], outline=CREMA2+(90,), width=1)
    diamond(d, 60, H//2, 11, TEAL+(255,)); diamond(d, W-60, H//2, 11, TEAL+(255,))
    els['c_ring'] = im
    im, d = new_layer()
    lg = Image.open(LOGO).convert('RGBA').resize((230, 230), Image.LANCZOS)
    im.paste(lg, (W//2-115, 150), lg)
    els['c_logo'] = im
    im, d = new_layer()
    draw_tracked(d, W//2, 430, 'HORAS DISPONIBLES', cin(78), 9, CREMA)
    separator(d, 560)
    els['c_title'] = im
    im, d = new_layer()
    draw_tracked(d, W//2, 620, 'LUNES A DOMINGO', mon(34), 6, CREMA2)
    s = fit_size('10:00 — 20:00 HRS', 96, .05, 900, cin)
    draw_tracked(d, W//2, 690, '10:00 — 20:00 HRS', cin(s), int(s*.05), CREMA)
    els['c_hours'] = im
    im, d = new_layer()
    draw_tracked(d, W//2, 830, 'DOMINGO ABIERTO CON RESERVA PREVIA', mon(29), 3, TEAL_L)
    els['c_note'] = im
    im, d = new_layer()
    draw_tracked(d, W//2, 950, 'JOSÉ JOAQUÍN PÉREZ 528, SAN BERNARDO', mon(30), 4, CREMA)
    draw_tracked(d, W//2, 1010, '+56 9 4778 6839', mon(30), 4, CREMA2)
    draw_tracked(d, W//2, 1070, '@ABYSS_TATTOO_STUDIO', mon(30), 4, TEAL_L)
    els['c_contact'] = im
    im, d = new_layer()
    txt = 'CÓMO LLEGAR · WHATSAPP'
    f = mon(30); tr = 5
    tw = tracked_width(d, txt, f, tr)
    pw, ph = tw+120, 92
    x0, y0 = (W-pw)//2, 1240-ph//2
    d.rounded_rectangle([x0, y0, x0+pw, y0+ph], radius=ph//2, outline=TEAL_L+(255,), width=2)
    diamond(d, x0+38, 1240, 7, TEAL_L+(255,)); diamond(d, x0+pw-38, 1240, 7, TEAL_L+(255,))
    draw_tracked(d, W//2, 1240-21, txt, f, tr, CREMA)
    els['c_cta'] = im
    im, d = new_layer()
    draw_tracked(d, W//2, H-160, 'TE ESPERAMOS EN EL BARRIO · ABYSS TATTOO', mon(26), 4, CREMA3)
    els['c_foot'] = im
    return els

def build():
    os.makedirs(OV, exist_ok=True)
    for k, im in ov_aerial().items(): im.save(f'{OV}/a__{k}.png')
    for k, im in ov_shots().items(): im.save(f'{OV}/s__{k}.png')
    for k, im in ov_card().items(): im.save(f'{OV}/{k}.png')
    print('overlays ok', flush=True)

def compose():
    inputs, fc = [], []
    nin = [0]
    def ain(t):
        inputs.extend(t); i = nin[0]; nin[0] += 1; return i
    shots = [
        dict(src=f'{OUT}/aerial_graded.jpg', z=(1.26, 1.02)),
        dict(src=f'{OUT}/m_night.jpg', z=(1.00, 1.14)),
        dict(src=f'{OUT}/m_day.jpg',  z=(1.12, 1.00)),
        dict(src=f'{OUT}/m_vitrina.jpg', z=(1.00, 1.16)),
    ]
    for i, sh in enumerate(shots):
        dur = DS[i] + (TR_[i] if i < 3 else 0)
        ain(['-loop', '1', '-t', f'{dur:.2f}', '-i', sh['src']])
        dn = int(dur*30); z0, z1 = sh['z']
        fc.append(f"[{i}:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='{z0}+({z1}-{z0})*on/{dn}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={dn}:s=1080x1920:fps=30,format=rgba[s{i}]")
    fc.append(f"[s0][s1]xfade=transition=fade:duration={TR_[0]}:offset={O1}[x1]")
    fc.append(f"[x1][s2]xfade=transition=slideup:duration={TR_[1]}:offset={O2}[x2]")
    fc.append(f"[x2][s3]xfade=transition=circleopen:duration={TR_[2]}:offset={O3}[x3]")
    fc.append(f"color=c=0x292521:s=1080x1920:r=30:d=12.0,format=rgba[vc];[x3][vc]blend=all_mode=normal:all_opacity=0.34:shortest=1[bv]")
    tl = [('a__eyebrow', 0.55, 0.5, 'down', 3.0), ('a__h1a', 0.85, 0.55, 'back', 3.0),
          ('a__h1b', 1.10, 0.55, 'back', 3.0), ('a__pin', 1.70, 0.6, 'pin', 3.0),
          ('a__chip', 2.30, 0.5, 'up', 3.0), ('s__cap_aerial', 1.4, 0.5, 'cap', 3.0),
          ('s__cap_night', 3.7, 0.5, 'cap', 5.7), ('s__cap_day', 6.4, 0.5, 'cap', 8.3),
          ('s__cap_vitrina', 9.1, 0.5, 'cap', 10.9)]
    ov = '[bv]'; j = 0
    for name, stt, dd, kind, tout in tl:
        ii = ain(['-loop', '1', '-t', f'{TOTAL:.2f}', '-i', f'{OV}/{name}.png'])
        p = P(stt, dd); ex = f"-260*{quadin(P(T_EXIT,0.25))}"
        fade = f"format=rgba,fade=t=in:st={stt}:d={dd*0.6}:alpha=1,fade=t=out:st={tout}:d=0.3:alpha=1"
        if kind == 'down':   xy = f"x=0:y='(-90)*{cubic(p)}{ex}'"
        elif kind == 'back': xy = f"x=0:y='150*{back(p)}{ex}'"
        elif kind == 'pin':  xy = f"x=0:y='-320*{back(p)}{ex}'"
        elif kind == 'cap':  xy = f"x=0:y='70*{cubic(p)}{ex}'"
        else:                xy = f"x=0:y='110*{back(p)}{ex}'"
        fc.append(f"[{ii}:v]{fade}[t{j}];{ov}[t{j}]overlay={xy}[o{j}a]")
        if name == 'a__pin':
            ii2 = ain(['-loop', '1', '-t', f'{TOTAL:.2f}', '-i', f'{OV}/a__pulse.png'])
            fc.append(f"[{ii2}:v]format=rgba,fade=t=in:st=2.1:d=0.5:alpha=1,fade=t=out:st=2.9:d=0.4:alpha=1[pz];[o{j}a][pz]overlay=0:0[o{j}]")
        else:
            fc.append(f"[o{j}a]copy[o{j}]")
        ov = f'[o{j}]'; j += 1
    fc.append(f"{ov}fade=t=in:st=0:d=0.35,format=yuv420p[vout]")
    cmdA = [FF, '-y', '-loglevel', 'error'] + inputs + [
        '-filter_complex', ';'.join(fc), '-map', '[vout]', '-t', f'{O4+TR_[3]:.2f}',
        '-r', '30', '-c:v', 'libx264', '-crf', '16', '-preset', 'fast', '-an',
        f'/tmp/main_ubic.mp4']
    # card
    eci, ecf = [], []
    en = [0]
    def ein(t):
        eci.extend(t); i = en[0]; en[0] += 1; return i
    base = ein(['-f', 'lavfi', '-t', '3.4', '-i', 'color=c=0x292521:s=1080x1920:r=30'])
    seq = [('c_ring', 0.08, 'fix'), ('c_logo', 0.18, 70), ('c_title', 0.45, 110),
           ('c_hours', 0.75, 90), ('c_note', 1.05, 70), ('c_contact', 1.30, 70),
           ('c_cta', 1.60, 90), ('c_foot', 1.95, 'fix')]
    prev = f'[{base}:v]'
    for k, (name, tt, mv) in enumerate(seq):
        ii = ein(['-loop', '1', '-t', '3.4', '-i', f'{OV}/{name}.png'])
        ecf.append(f"[{ii}:v]format=rgba,fade=t=in:st={tt}:d=0.4:alpha=1[e{k}]")
        if mv == 'fix':
            ecf.append(f"{prev}[e{k}]overlay=0:0[ec{k}]")
        else:
            ecf.append(f"{prev}[e{k}]overlay=x=0:y='{mv}*{back(P(tt,0.6))}'[ec{k}]")
        prev = f'[ec{k}]'
    ecf.append(f"{prev}format=yuv420p[ecout]")
    cmdB = [FF, '-y', '-loglevel', 'error'] + eci + [
        '-filter_complex', ';'.join(ecf), '-map', '[ecout]', '-t', '3.4', '-r', '30',
        '-c:v', 'libx264', '-crf', '16', '-preset', 'fast', '-an', f'/tmp/ec_ubic.mp4']
    cmdC = [FF, '-y', '-loglevel', 'error', '-i', '/tmp/main_ubic.mp4', '-i', '/tmp/ec_ubic.mp4',
            '-filter_complex',
            f"[0:v][1:v]xfade=transition=slideleft:duration={TR_[3]}:offset={O4},fade=t=out:st={TOTAL-0.4}:d=0.4,format=yuv420p[vout]",
            '-map', '[vout]', '-t', f'{TOTAL:.2f}', '-r', '30', '-c:v', 'libx264',
            '-crf', '18', '-preset', 'fast', '-an', '-movflags', '+faststart',
            f'{OUT}/story_ubicacion_aerea.mp4']
    return cmdA, cmdB, cmdC

if __name__ == '__main__':
    build()
    for cmd in compose():
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            print('ERROR'); print(r.stderr[-2500:]); sys.exit(1)
    print('render ok', flush=True)
