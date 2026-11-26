"""サンプル画像（架空・模式図）を SVG data URL で生成する。
実際の患者画像ではなく、画面確認用に描いたイラストです。LocalStorage 容量を考慮し 1 枚数 KB に抑えています。
"""
import base64, math, random

W, H = 512, 384


def url(svg: str) -> str:
    return 'data:image/svg+xml;base64,' + base64.b64encode(svg.encode('utf-8')).decode()


def _wrap(body, bg='#000', defs='', label='', label_color='#e0e0e0'):
    return url(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
               f'<defs>{defs}</defs><rect width="{W}" height="{H}" fill="{bg}"/>{body}'
               f'<text x="10" y="{H - 10}" fill="{label_color}" font-family="sans-serif" font-size="13">{label}</text></svg>')


NOISE = ('<filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="{seed}"/>'
         '<feColorMatrix values="0 0 0 0 .5  0 0 0 0 .5  0 0 0 0 .5  0 0 0 .35 0"/></filter>'
         '<filter id="b"><feGaussianBlur stdDeviation="1.6"/></filter>'
         '<radialGradient id="v" cx="50%" cy="50%" r="65%"><stop offset="0" stop-color="#bdbdbd"/><stop offset="1" stop-color="#6e6e6e"/></radialGradient>')

# 血管走行（模式）: name -> 点列
TREES = {
    'LCA': {
        'main': [(250, 40), (255, 90), (240, 120)],
        'LAD': [(240, 120), (215, 170), (190, 230), (170, 290), (160, 345)],
        'LCX': [(240, 120), (300, 150), (350, 190), (380, 250), (390, 300)],
        'D1': [(205, 190), (150, 215), (110, 250)],
        'OM': [(330, 175), (355, 225), (345, 280)],
    },
    'RCA': {
        'main': [(150, 60), (200, 70), (250, 95), (300, 140), (330, 200), (335, 260), (310, 310)],
        'PD': [(310, 310), (260, 330), (200, 345)],
        'PL': [(310, 310), (360, 320), (400, 335)],
        'RV': [(250, 95), (220, 150), (205, 200)],
    },
    'SFA': {
        'main': [(250, 20), (255, 120), (262, 220), (270, 330), (275, 370)],
        'DFA': [(252, 70), (220, 140), (200, 230)],
    },
}
WIDTH = {'main': 11, 'LAD': 8, 'LCX': 8, 'D1': 5, 'OM': 5, 'PD': 5, 'PL': 5, 'RV': 4, 'DFA': 7}


def _path(pts):
    d = f'M{pts[0][0]},{pts[0][1]}'
    for i in range(1, len(pts) - 1):
        mx, my = (pts[i][0] + pts[i + 1][0]) / 2, (pts[i][1] + pts[i + 1][1]) / 2
        d += f' Q{pts[i][0]},{pts[i][1]} {mx},{my}'
    return d + f' L{pts[-1][0]},{pts[-1][1]}'


def _along(pts, t):
    seg = len(pts) - 1
    i = min(int(t * seg), seg - 1)
    f = t * seg - i
    return pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f


def angio(label, tree='LCA', lesions=(), occluded=None, stent=None, seed=1, collateral=False):
    """シネアンギオ（陰性像風：背景暗・血管明）
    lesions: [(branch, t, severity 0-1)], occluded: (branch, t) 以遠は描かない, stent: (branch, t0, t1)"""
    br = TREES[tree]
    body = '<g filter="url(#b)">'
    # カテーテル
    s = br['main'][0]
    body += f'<path d="M{s[0] - 4},{-10} Q{s[0] - 30},{s[1] - 10} {s[0]},{s[1]}" stroke="#9e9e9e" stroke-width="5" fill="none"/>'
    for name, pts in br.items():
        p = list(pts)
        distal_dim = ''
        if occluded and occluded[0] == 'main' and name != 'main':
            if not collateral:
                continue
            distal_dim = ' opacity=".45"'  # 側副血行路からの逆行性造影
        if occluded and occluded[0] == name:
            cut = _along(pts, occluded[1])
            n = max(1, int(occluded[1] * (len(pts) - 1)) + 1)
            p = pts[:n] + [cut]
        body += f'<path d="{_path(p)}" stroke="url(#v)" stroke-width="{WIDTH.get(name, 5)}" fill="none" stroke-linecap="round"{distal_dim}/>'
    for name, t, sev in lesions:
        x, y = _along(br[name], t)
        w = WIDTH.get(name, 5)
        body += f'<ellipse cx="{x}" cy="{y}" rx="{w * 0.55}" ry="{w * 0.9 * sev}" fill="#141414" transform="rotate(35 {x} {y})"/>'
    body += '</g>'
    if stent:
        name, t0, t1 = stent
        p = [_along(br[name], t0 + (t1 - t0) * k / 8) for k in range(9)]
        body += f'<path d="{_path(p)}" stroke="#e0e0e0" stroke-width="{WIDTH.get(name, 5) + 3}" fill="none" stroke-dasharray="2 2" opacity=".55"/>'
    if collateral:
        body += '<path d="M190,230 C240,260 280,300 300,330" stroke="#8a8a8a" stroke-width="2" fill="none" stroke-dasharray="1 3" filter="url(#b)"/>'
    for name, t, sev in lesions:
        x, y = _along(br[name], t)
        body += f'<circle cx="{x}" cy="{y}" r="18" fill="none" stroke="#ffcc00" stroke-width="2" stroke-dasharray="5 4"/>'
    if occluded:
        x, y = _along(br[occluded[0]], occluded[1])
        body += f'<path d="M{x - 12},{y - 12} L{x + 12},{y + 12} M{x + 12},{y - 12} L{x - 12},{y + 12}" stroke="#ff5252" stroke-width="2"/>'
    body += f'<rect width="{W}" height="{H}" filter="url(#n)"/>'
    return _wrap(body, '#1a1a1a', NOISE.format(seed=seed), label)


def lvg(label, phase='diastole', ef=60, akinetic_apex=False):
    sc = 1.0 if phase == 'diastole' else math.sqrt(1 - ef / 100) * 1.05
    rx, ry = 95 * sc, 130 * sc
    apex = '' if not (akinetic_apex and phase == 'systole') else f'<ellipse cx="270" cy="{190 + ry * 0.85}" rx="40" ry="35" fill="url(#v)"/>'
    body = (f'<g filter="url(#b)"><path d="M260,0 Q240,120 250,160 Q262,250 282,300" stroke="#9e9e9e" stroke-width="4" fill="none"/>'
            f'<ellipse cx="260" cy="190" rx="{rx}" ry="{ry}" fill="url(#v)" transform="rotate(-25 260 190)"/>{apex}'
            f'<circle cx="282" cy="306" r="9" stroke="#9e9e9e" stroke-width="3" fill="none"/></g>'
            f'<rect width="{W}" height="{H}" filter="url(#n)"/>'
            f'<text x="{W - 10}" y="24" fill="#ffcc00" font-family="sans-serif" font-size="14" text-anchor="end">{phase} EF {ef}%</text>')
    return _wrap(body, '#1a1a1a', NOISE.format(seed=11), label)


def ivus(label, plaque_deg=200, calc_deg=0, oct=False, stent=False, seed=3):
    tint = '#ff9f43' if oct else '#d0d0d0'
    lumen_r = 42 if not stent else 62
    a0, a1 = -60, -60 + plaque_deg
    def arc(r, a, b):
        x0, y0 = 256 + r * math.cos(math.radians(a)), 192 + r * math.sin(math.radians(a))
        x1, y1 = 256 + r * math.cos(math.radians(b)), 192 + r * math.sin(math.radians(b))
        return f'M{x0:.1f},{y0:.1f} A{r},{r} 0 {1 if b - a > 180 else 0} 1 {x1:.1f},{y1:.1f}'
    struts = ''.join(f'<rect x="{256 + 62 * math.cos(k * 0.52) - 3:.1f}" y="{192 + 62 * math.sin(k * 0.52) - 3:.1f}" width="6" height="6" fill="#fff"/>' for k in range(12)) if stent else ''
    calc = f'<path d="{arc(80, 30, 30 + calc_deg)}" stroke="#fff" stroke-width="7" fill="none"/><path d="{arc(110, 30, 30 + calc_deg)}" stroke="#000" stroke-width="40" fill="none" opacity=".8"/>' if calc_deg else ''
    body = (f'<circle cx="256" cy="192" r="150" fill="#202020"/>'
            f'<circle cx="256" cy="192" r="118" fill="none" stroke="{tint}" stroke-width="6" opacity=".7"/>'
            f'<path d="{arc(85, a0, a1)}" stroke="{tint}" stroke-width="44" fill="none" opacity=".45"/>'
            f'{calc}<circle cx="256" cy="192" r="{lumen_r}" fill="#050505" stroke="{tint}" stroke-width="2"/>{struts}'
            f'<circle cx="245" cy="198" r="7" fill="#aaa"/>'
            f'<rect width="{W}" height="{H}" filter="url(#n)" opacity=".9"/>'
            f'<line x1="430" y1="350" x2="480" y2="350" stroke="#fff" stroke-width="2"/><text x="455" y="343" fill="#fff" font-size="11" text-anchor="middle" font-family="sans-serif">1 mm</text>')
    return _wrap(body, '#000', NOISE.format(seed=seed), label)


def ecg12(label, st_leads=(), rhythm='sinus'):
    leads = ['I', 'II', 'III', 'aVR', 'aVL', 'aVF', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6']
    grid = ''.join(f'<line x1="{i}" y1="0" x2="{i}" y2="{H}" stroke="#f3c6c6" stroke-width="{1 if i % 40 == 0 else .4}"/>' for i in range(0, W + 1, 8))
    grid += ''.join(f'<line x1="0" y1="{i}" x2="{W}" y2="{i}" stroke="#f3c6c6" stroke-width="{1 if i % 40 == 0 else .4}"/>' for i in range(0, H + 1, 8))
    rnd = random.Random(5)
    body = grid
    for idx, ld in enumerate(leads):
        col, row = idx // 3, idx % 3
        x0, y0 = 8 + col * 126, 70 + row * 110
        pts, x = [], x0
        st = 24 if ld in st_leads else (-8 if (st_leads and ld in ('I', 'aVL') and 'III' in st_leads) else 0)
        inv = -1 if ld == 'aVR' else 1
        while x < x0 + 118:
            if rhythm == 'vf':
                pts.append((x, y0 + rnd.uniform(-22, 22)))
                x += 4
                continue
            pts += [(x, y0), (x + 8, y0), (x + 11, y0 - 5 * inv), (x + 14, y0), (x + 18, y0), (x + 20, y0 + 6 * inv), (x + 23, y0 - 40 * inv),
                    (x + 26, y0 + 12 * inv), (x + 29, y0 - st), (x + 38, y0 - st - 8 * inv), (x + 46, y0 - st * .3), (x + 52, y0)]
            x += 56
        d = 'M' + ' L'.join(f'{a:.0f},{b:.0f}' for a, b in pts if a < x0 + 120)
        body += f'<path d="{d}" stroke="#111" stroke-width="1.3" fill="none"/><text x="{x0 + 2}" y="{y0 - 34}" font-size="11" font-family="sans-serif" fill="#900">{ld}</text>'
    return _wrap(body, '#fff8f8', '', label, '#900')


def chest_xp(label, congestion=False, devices=False):
    hazy = '<ellipse cx="170" cy="200" rx="70" ry="90" fill="#bbb" opacity=".35"/><ellipse cx="340" cy="200" rx="70" ry="90" fill="#bbb" opacity=".35"/>' if congestion else ''
    dev = ('<path d="M300,384 L300,250 Q300,200 280,160" stroke="#fff" stroke-width="4" fill="none"/>'
           '<path d="M330,384 L320,300 Q300,240 300,200" stroke="#eee" stroke-width="3" fill="none"/>') if devices else ''
    body = (f'<g filter="url(#b)"><ellipse cx="170" cy="200" rx="85" ry="135" fill="#2d2d2d"/><ellipse cx="340" cy="200" rx="85" ry="135" fill="#2d2d2d"/>'
            f'<rect x="246" y="20" width="20" height="200" fill="#9e9e9e"/><ellipse cx="290" cy="245" rx="95" ry="75" fill="#c8c8c8"/>{hazy}'
            + ''.join(f'<path d="M{255 - k},{60 + k * 22} Q{150},{40 + k * 26} {95},{110 + k * 22}" stroke="#777" stroke-width="5" fill="none"/>'
                      f'<path d="M{260 + k},{60 + k * 22} Q{360},{40 + k * 26} {415},{110 + k * 22}" stroke="#777" stroke-width="5" fill="none"/>' for k in range(8))
            + f'</g>{dev}<rect width="{W}" height="{H}" filter="url(#n)"/>'
            f'<text x="{W - 12}" y="24" fill="#fff" font-size="16" font-family="sans-serif" text-anchor="end">R</text>')
    return _wrap(body, '#0e0e0e', NOISE.format(seed=21), label)


def ucg(label, view='PLAX', note=''):
    body = (f'<path d="M256,30 L80,330 A260,260 0 0 0 432,330 Z" fill="#141414"/>'
            f'<g filter="url(#b)" opacity=".9"><path d="M120,200 Q256,150 400,210" stroke="#bbb" stroke-width="18" fill="none"/>'
            f'<path d="M120,290 Q256,330 400,280" stroke="#aaa" stroke-width="22" fill="none"/>'
            f'<ellipse cx="300" cy="240" rx="40" ry="18" fill="none" stroke="#eee" stroke-width="6"/></g>'
            f'<path d="M256,30 L80,330 A260,260 0 0 0 432,330 Z" filter="url(#n)"/>'
            f'<text x="12" y="24" fill="#4fc3f7" font-size="14" font-family="sans-serif">{view}</text>'
            f'<text x="{W - 12}" y="24" fill="#ffcc00" font-size="13" font-family="sans-serif" text-anchor="end">{note}</text>')
    return _wrap(body, '#000', NOISE.format(seed=31), label)


def ccta(label, stenosis_at=0.5, calc=True):
    pts = [(80, 80), (180, 140), (280, 190), (380, 250), (450, 320)]
    x, y = _along(pts, stenosis_at)
    body = (f'<rect x="20" y="20" width="472" height="330" fill="#1c1c1c"/>'
            f'<g filter="url(#b)"><path d="{_path(pts)}" stroke="#9e9e9e" stroke-width="22" fill="none" stroke-linecap="round"/>'
            f'<path d="{_path(pts)}" stroke="#d6d6d6" stroke-width="10" fill="none" stroke-linecap="round"/>'
            f'<ellipse cx="{x}" cy="{y}" rx="9" ry="6" fill="#6e6e6e" transform="rotate(30 {x} {y})"/>'
            + (f'<circle cx="{x + 14}" cy="{y - 10}" r="6" fill="#fff"/>' if calc else '') +
            f'</g><rect width="{W}" height="{H}" filter="url(#n)"/>'
            f'<text x="{W - 12}" y="24" fill="#4fc3f7" font-size="13" font-family="sans-serif" text-anchor="end">CPR</text>')
    return _wrap(body, '#000', NOISE.format(seed=41), label)


def pressure_trace(label, ffr=0.78, ifr=None):
    def wave(base, amp, phase=0):
        return 'M' + ' L'.join(f'{x},{base - amp * max(0, math.sin((x / 60 + phase) * math.pi)) ** 1.5 - amp * 0.25 * math.sin(x / 60 * 2 * math.pi):.1f}' for x in range(20, 500, 3))
    body = (''.join(f'<line x1="20" y1="{y}" x2="500" y2="{y}" stroke="#2b3a42" stroke-width="1"/>' for y in range(60, 340, 40)) +
            f'<path d="{wave(240, 90)}" stroke="#e53935" stroke-width="2" fill="none"/>'
            f'<path d="{wave(240 + (1 - ffr) * 120, 90 * ffr)}" stroke="#ffeb3b" stroke-width="2" fill="none"/>'
            f'<text x="24" y="34" fill="#e53935" font-size="13" font-family="sans-serif">Pa</text>'
            f'<text x="60" y="34" fill="#ffeb3b" font-size="13" font-family="sans-serif">Pd</text>'
            f'<rect x="360" y="14" width="140" height="{56 if ifr else 34}" fill="#000" stroke="#4fc3f7"/>'
            f'<text x="430" y="38" fill="#4fc3f7" font-size="18" font-family="sans-serif" text-anchor="middle">FFR {ffr:.2f}</text>'
            + (f'<text x="430" y="62" fill="#4fc3f7" font-size="14" font-family="sans-serif" text-anchor="middle">iFR {ifr:.2f}</text>' if ifr else ''))
    return _wrap(body, '#0b1820', '', label, '#cfd8dc')


def scinti(label, defect=('anterior',)):
    seg = {'anterior': (-135, -45), 'lateral': (-45, 45), 'inferior': (45, 135), 'septal': (135, 225)}
    body = ''
    for ring, r in enumerate((150, 110, 70)):
        for name, (a, b) in seg.items():
            col = '#1e3cff' if name in defect and ring < 2 else ('#ffb300' if name in defect else '#e53935')
            x0, y0 = 256 + r * math.cos(math.radians(a)), 192 + r * math.sin(math.radians(a))
            x1, y1 = 256 + r * math.cos(math.radians(b)), 192 + r * math.sin(math.radians(b))
            body += f'<path d="M256,192 L{x0:.1f},{y0:.1f} A{r},{r} 0 0 1 {x1:.1f},{y1:.1f} Z" fill="{col}" stroke="#000" stroke-width="1"/>'
    body += '<circle cx="256" cy="192" r="30" fill="#ff7043" stroke="#000"/>'
    body += '<text x="256" y="30" fill="#fff" font-size="12" text-anchor="middle" font-family="sans-serif">ANT</text>'
    return _wrap(body, '#000', '', label)
