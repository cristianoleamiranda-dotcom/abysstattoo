#!/usr/bin/env python3
"""
Abyss Reels PRO — edición multicámara 1080x1920 · 14 s · 30 fps.
Técnica aplicada (investigación motion 2025-26):
  * hook ≤3 s: toma macro con speed-ramp 1.33x + movimiento inmediato
  * cortes cada 2.4-2.8 s con zoom punch alternado (in/out) y drift Ken Burns
  * transiciones motivadas: fade → slideup → circleopen → whip slideleft a end card
  * kinetic typography: stagger 0.25-0.45 s, ease-out-back en héroes, ease-out-cubic
    en filas, ease-in quad de salida antes del whip; holds de lectura intermedios
  * CTA animado: pop ease-out-back + float senoidal continuo
  * zonas seguras: nada crítico sobre y<269 ni bajo y>1400
Salida: material/reels/reel_*.mp4 (sobrescribe finales)
"""
import os, sys, subprocess
from PIL import Image, ImageDraw
sys.path.insert(0, 'material/pipeline')
from stories import (W, H, CARBON, CREMA, CREMA2, CREMA3, TEAL, TEAL_L, LOGO,
                     cin, mon, tracked_width, draw_tracked, fit_size,
                     diamond, separator)
from stories_v2 import day_row, stamp
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()

OUT = 'material/reels'
OV  = f'{OUT}/overlays_pro'
VID = 'material/editado/vid'
IMG = 'material/editado/img'

# ---------- timing global ----------
D_SHOTS = [2.4, 2.6, 2.8, 4.0]          # + end card 3.5
TR = [0.30, 0.32, 0.38, 0.28]           # duraciones xfade (última = whip)
O1 = D_SHOTS[0] - TR[0]                  # 2.10
O2 = O1 + D_SHOTS[1] - TR[1]             # 4.38
O3 = O2 + D_SHOTS[2] - TR[2]             # 6.80
O4 = O3 + D_SHOTS[3] - TR[3]             # 10.52  (whip a end card)
TOTAL = O4 + 3.5                         # 14.02
T_EXIT = 10.15                           # salida de type antes del whip

def P(st, d):   # progreso clippeado
    return f"min(max((t-{st})/{d},0),1)"
def back(p):    # 1-easeOutBack  (offset relativo)
    return f"(-2.70158*pow({p}-1,3)-1.70158*pow({p}-1,2))"
def cubic(p):   # 1-easeOutCubic
    return f"pow(1-{p},3)"
def quadin(p):  # easeInQuad
    return f"pow({p},2)"

def new_layer():
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)

# ---------- elementos tipográficos (posiciones finales, zona segura) ----------
def el_eyebrow(txt):
    im, d = new_layer()
    lg = Image.open(LOGO).convert('RGBA').resize((150, 150), Image.LANCZOS)
    im.paste(lg, (W//2-75, 210), lg)
    draw_tracked(d, W//2, 402, txt, mon(27, 600), 9, CREMA2)
    return im

def el_h1(lines):
    out = []
    y = 470
    for line in lines:
        im, d = new_layer()
        s = fit_size(line, 122, .12, 900, cin)
        draw_tracked(d, W//2, y, line, cin(s, 700), int(s*.12), CREMA)
        out.append(im); y += int(s*1.14)
    return out

def el_body(st):
    """devuelve lista de (nombre, im) con cursor compacto desde y=760"""
    res = []
    nrow = 0
    if st.get('stamp_first'):
        im, d = new_layer(); stamp(im, 945, st['stamp_first']); res.append(('row1', im))
        y = 740 + 430; nrow = 1
    else:
        y = 760
    for kind, payload in st['body']:
        if kind == 'row':
            im, d = new_layer(); nrow += 1
            y += 34; y = day_row(d, y, *payload) + (26 if nrow == 1 else 40)
            res.append((f'row{nrow}', im))
        elif kind == 'hours':
            im, d = new_layer()
            s = fit_size(payload, 84, .05, 900, cin)
            draw_tracked(d, W//2, y, payload, cin(s, 700), int(s*.05), CREMA)
            y += s + (30 if st.get('tight') else 44)
            res.append((f'hours{nrow}', im))
        elif kind == 'line':
            im, d = new_layer()
            draw_tracked(d, W//2, y, payload[0], mon(payload[1], 400), 2, CREMA2)
            y += payload[1] + 48
            res.append(('line', im))
        elif kind == 'note':
            im, d = new_layer()
            draw_tracked(d, W//2, y, payload, mon(29, 600), 3, TEAL_L)
            y += 62
            res.append(('note', im))
    return res, y

def el_cta(txt, cy=1360):
    im, d = new_layer()
    f = mon(30, 600); tr = 5
    tw = tracked_width(d, txt, f, tr)
    pw, ph = tw+120, 92
    x0, y0 = (W-pw)//2, cy-ph//2
    d.rounded_rectangle([x0, y0, x0+pw, y0+ph], radius=ph//2, outline=TEAL_L+(255,), width=2)
    diamond(d, x0+38, cy, 7, TEAL_L+(255,))
    diamond(d, x0+pw-38, cy, 7, TEAL_L+(255,))
    draw_tracked(d, W//2, cy-21, txt, f, tr, CREMA)
    return im

def el_endcard(st):
    ring, d = new_layer()
    d.rectangle([54, 54, W-55, H-55], outline=CREMA2+(255,), width=2)
    d.rectangle([66, 66, W-67, H-67], outline=CREMA2+(90,), width=1)
    d.ellipse([W//2-300, 480, W//2+300, 1080], outline=CREMA2+(120,), width=1)
    diamond(d, 60, H//2, 11, TEAL+(255,)); diamond(d, W-60, H//2, 11, TEAL+(255,))
    logo, _ = new_layer()
    lg = Image.open(LOGO).convert('RGBA').resize((280, 280), Image.LANCZOS)
    logo.paste(lg, (W//2-140, 560), lg)
    title, d = new_layer(); draw_tracked(d, W//2, 900, 'RESERVA TU HORA', cin(74, 700), 9, CREMA)
    separator(d, 1030)
    cta, d = new_layer(); draw_tracked(d, W//2, 1080, st['cta'], mon(32, 600), 5, CREMA)
    addr, d = new_layer(); draw_tracked(d, W//2, 1170, 'JOSÉ JOAQUÍN PÉREZ 528, SAN BERNARDO', mon(27, 600), 4, CREMA2)
    hnd, d = new_layer(); draw_tracked(d, W//2, 1220, '@ABYSS_TATTOO_STUDIO', mon(27, 600), 4, TEAL_L)
    note, d = new_layer(); draw_tracked(d, W//2, H-160, 'DOMINGO ABIERTO CON RESERVA PREVIA', mon(26, 600), 4, CREMA3)
    return [('ec_ring', ring), ('ec_logo', logo), ('ec_title', title),
            ('ec_cta', cta), ('ec_addr', addr), ('ec_handle', hnd), ('ec_note', note)]

STORIES = [
    dict(key='reel_1_agenda_semanal', veil=0.42,
         shots=[dict(src=f'{VID}/vid-20261011-wa0007.mp4', ss=0.4, z=(1.14, 1.00), ramp=0.75),
                dict(src=f'{VID}/img_34542.mp4',          ss=0.5, z=(1.00, 1.12)),
                dict(src=f'{VID}/img_47642.mp4',          ss=0.8, z=(1.14, 1.02)),
                dict(src=f'{VID}/img_19572.mp4',          ss=0.6, z=(1.00, 1.10))],
         eyebrow='ABYSS TATTOO Y PIERCING · SAN BERNARDO', h1=['AGENDA', 'SEMANAL'],
         body=[('row', ('TATUAJE · TODOS LOS DÍAS', {0, 1, 2, 3, 4, 5, 6})),
               ('hours', '10:00 — 20:00 HRS'),
               ('row', ('PIERCING · MA A SÁ', {1, 2, 3, 4, 5})),
               ('hours', '12:00 — 19:00 HRS')],
         tight=True, cta='RESERVA TU HORA · WHATSAPP'),
    dict(key='reel_2_domingo_abierto', veil=0.52,
         shots=[dict(src=f'{VID}/vid-20261011-wa0009.mp4', ss=0.3, z=(1.16, 1.02), ramp=0.75),
                dict(src=f'{VID}/img_19522.mp4',          ss=0.5, z=(1.00, 1.14)),
                dict(src=f'{VID}/vid-20261011-wa0002.mp4', ss=0.7, z=(1.12, 1.00)),
                dict(src=f'{VID}/vid-20261011-wa0008.mp4', ss=0.6, z=(1.00, 1.08))],
         eyebrow='UN SOLO DÍA · CUPOS LIMITADOS', h1=['DOMINGO', 'ABIERTO'],
         stamp_first='CON RESERVA PREVIA',
         body=[('hours', '10:00 — 20:00 HRS'),
               ('note', 'SIN RESERVA NO HAY ATENCIÓN DOMINICAL')],
         cta='ESCRÍBENOS · +56 9 4778 6839'),
    dict(key='reel_3_agenda_piercing', veil=0.45,
         shots=[dict(src=f'{IMG}/septum_macro.jpg',  z=(1.12, 1.00)),
                dict(src=f'{IMG}/oreja_cadena.jpg',  z=(1.00, 1.16)),
                dict(src=f'{IMG}/reel_piercing.jpg', z=(1.14, 1.02)),
                dict(src=f'{IMG}/oreja_cadena.jpg',  z=(1.05, 1.18), dx=0.10, dy=-0.08)],
         eyebrow='ABYSS PIERCING', h1=['AGENDA', 'PIERCING'],
         body=[('line', ('SEPTUM · LÓBULO · CARTÍLAGO · DERMOIDE', 30)),
               ('row', ('MA A SÁ · RESERVA PREVIA', {1, 2, 3, 4, 5})),
               ('hours', '12:00 — 19:00 HRS'),
               ('note', 'TATUAJE: LUNES A DOMINGO 10:00 — 20:00')],
         cta='RESERVA TU HORA · WHATSAPP'),
]

def build_overlays(st):
    els = [('eyebrow', el_eyebrow(st['eyebrow']))]
    for i, im in enumerate(el_h1(st['h1'])):
        els.append((f'h1{i}', im))
    body = el_body(st)[0]
    st['body_order'] = [n for n, _ in body]
    els += body
    els.append(('cta', el_cta(st['cta'])))
    els += el_endcard(st)
    os.makedirs(OV, exist_ok=True)
    for name, im in els:
        im.save(f'{OV}/{st["key"]}__{name}.png', optimize=True)
    return [n for n, _ in els]

# ---------- composición ffmpeg ----------
def compose(st):
    """devuelve (cmdA, cmdB, cmdC)"""
    key = st['key']
    inputs, fc = [], []
    nin = [0]
    def ain(tokens):
        inputs.extend(tokens); i = nin[0]; nin[0] += 1; return i
    for i, sh in enumerate(st['shots']):
        dur = D_SHOTS[i] + TR[i] if i < 3 else D_SHOTS[3]
        if sh['src'].endswith('.mp4'):
            ain(['-ss', str(sh['ss']), '-t', f"{dur*(sh.get('ramp',1))+0.4:.2f}", '-i', sh['src']]
)
            ramp = f"setpts=(PTS-STARTPTS)*{sh['ramp']}," if sh.get('ramp') else 'setpts=PTS-STARTPTS,'
            z0, z1 = sh['z']
            fc.append(f"[{i}:v]{ramp}fps=30,scale=w='2*ceil((1080*({z0}+({z1}-{z0})*min(t/{dur},1)))/2)':h=-2:eval=frame,crop=1080:1920,format=rgba[s{i}]")
        else:
            ain(['-loop', '1', '-t', f'{dur:.2f}', '-i', sh['src']])
            dn = int(dur*30)
            z0, z1 = sh['z']
            dx, dy = sh.get('dx', 0), sh.get('dy', 0)
            xe = f"'iw/2-(iw/zoom/2)+iw*{dx}'" if dx else "'iw/2-(iw/zoom/2)'"
            ye = f"'ih/2-(ih/zoom/2)+ih*{dy}'" if dy else "'ih/2-(ih/zoom/2)'"
            fc.append(f"[{i}:v]zoompan=z='{z0}+({z1}-{z0})*on/{dn}':x={xe}:y={ye}:d={dn}:s=1080x1920:fps=30,format=rgba[s{i}]")
    fc.append(f"[s0][s1]xfade=transition=fade:duration={TR[0]}:offset={O1}[x1]")
    fc.append(f"[x1][s2]xfade=transition=slideup:duration={TR[1]}:offset={O2}[x2]")
    fc.append(f"[x2][s3]xfade=transition=circleopen:duration={TR[2]}:offset={O3}[x3]")
    fc.append(f"color=c=0x292521:s=1080x1920:r=30:d=11.0,format=rgba[vc];[x3][vc]blend=all_mode=normal:all_opacity={st['veil']}:shortest=1[bv]")
    timeline = [('eyebrow', 0.45, 0.5, 'down'), ('h10', 0.70, 0.55, 'back'),
                ('h11', 0.95, 0.55, 'back')]
    seq = 1.90
    for name in st.get('body_order', []):
        kind = 'left' if name == 'row1' else ('right' if name == 'row2' else 'up')
        timeline.append((name, seq, 0.5, kind)); seq += 0.45
    timeline.append(('cta', 5.40, 0.6, 'cta'))
    ov = '[bv]'
    for j, (name, stt, dd, kind) in enumerate(timeline):
        ii = ain(['-loop', '1', '-t', f'{TOTAL:.2f}', '-i', f'{OV}/{key}__{name}.png'])
        p = P(stt, dd)
        fade = f"format=rgba,fade=t=in:st={stt}:d={dd*0.6}:alpha=1"
        ex = f"-260*{quadin(P(T_EXIT,0.25))}"
        if kind == 'down':
            xy = f"x=0:y='(-90)*{cubic(p)}{ex}'"
        elif kind == 'back':
            xy = f"x=0:y='150*{back(p)}{ex}'"
        elif kind == 'left':
            xy = f"x='(-1080)*{cubic(p)}':y=0"
        elif kind == 'right':
            xy = f"x='1080*{cubic(p)}':y=0"
        elif kind == 'cta':
            xy = f"x=0:y='120*{back(p)}+7*sin(2*PI*(t-{stt})/2.6)*{p}{ex}'"
        else:
            xy = f"x=0:y='90*{cubic(p)}{ex}'"
        fc.append(f"[{ii}:v]{fade}[t{j}];{ov}[t{j}]overlay={xy}[o{j}]")
        ov = f'[o{j}]'
    n_main_inputs = nin[0]
    fc.append(f"{ov}fade=t=in:st=0:d=0.35,format=yuv420p[vout]")
    cmdA = [FF, '-y', '-loglevel', 'error'] + inputs + [
        '-filter_complex', ';'.join(fc), '-map', '[vout]', '-t', f'{O4+TR[3]:.2f}',
        '-r', '30', '-c:v', 'libx264', '-crf', '16', '-preset', 'fast',
        '-an', f'/tmp/main_{key}.mp4']
    # --- etapa B: end card 3.5 s
    eci, ecf = [], []
    en = [0]
    def ein(tokens):
        eci.extend(tokens); i = en[0]; en[0] += 1; return i
    base = ein(['-f', 'lavfi', '-t', '3.5', '-i', 'color=c=0x292521:s=1080x1920:r=30'])
    ec = ['ec_ring', 'ec_logo', 'ec_title', 'ec_cta', 'ec_addr', 'ec_handle', 'ec_note']
    ec_t = [0.10, 0.20, 0.55, 0.95, 1.25, 1.45, 1.80]
    prev = f'[{base}:v]'
    for j, (name, tt) in enumerate(zip(ec, ec_t)):
        ii = ein(['-loop', '1', '-t', '3.5', '-i', f'{OV}/{key}__{name}.png'])
        p = P(tt, 0.55)
        if name == 'ec_ring':
            ecf.append(f"[{ii}:v]format=rgba,fade=t=in:st={tt}:d=0.5:alpha=1,rotate=a='(-1.5708)*{cubic(p)}':ow=1080:oh=1920:c=none[e{j}]")
        else:
            ecf.append(f"[{ii}:v]format=rgba,fade=t=in:st={tt}:d=0.4:alpha=1[e{j}]")
        if name in ('ec_ring', 'ec_note'):
            ecf.append(f"{prev}[e{j}]overlay=0:0[ec{j}]")
        else:
            tr_v = 70 if name == 'ec_logo' else (110 if name == 'ec_title' else 70)
            ecf.append(f"{prev}[e{j}]overlay=x=0:y='{tr_v}*{back(P(tt,0.6))}'[ec{j}]")
        prev = f'[ec{j}]'
    ecf.append(f"{prev}format=yuv420p[ecout]")
    cmdB = [FF, '-y', '-loglevel', 'error'] + eci + [
        '-filter_complex', ';'.join(ecf), '-map', '[ecout]', '-t', '3.5',
        '-r', '30', '-c:v', 'libx264', '-crf', '16', '-preset', 'fast',
        '-an', f'/tmp/ec_{key}.mp4']
    # --- etapa C: whip slideleft main + ec + fade out
    cmdC = [FF, '-y', '-loglevel', 'error',
            '-i', f'/tmp/main_{key}.mp4', '-i', f'/tmp/ec_{key}.mp4',
            '-filter_complex',
            f"[0:v][1:v]xfade=transition=slideleft:duration={TR[3]}:offset={O4},fade=t=out:st={TOTAL-0.45}:d=0.45,format=yuv420p[vout]",
            '-map', '[vout]', '-t', f'{TOTAL:.2f}', '-r', '30', '-c:v', 'libx264',
            '-crf', '18', '-preset', 'fast', '-an', '-movflags', '+faststart',
            f'{OUT}/{key}.mp4']
    return cmdA, cmdB, cmdC


if __name__ == '__main__':
    for st in STORIES:
        build_overlays(st)
        print('overlays ok', st['key'], flush=True)
        for cmd in compose(st):
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode != 0:
                print('ERROR'); print(r.stderr[-2500:]); sys.exit(1)
        print('render ok', st['key'], flush=True)
