#!/usr/bin/env python3
"""サンプルデータ生成スクリプト（架空の患者・検査データ）

出力:
  sample-data/patients.json
  sample-data/reports.json
  sample-data/masters.json
各JSONはフロントエンド(LocalStorage初期データ)・Nodeバックエンド・Spring Bootバックエンドで共通利用する。
レポートは部分構造でよい（未指定項目は画面側で既定値により補完される）。
"""
import base64, json, os, random

random.seed(42)
OUT = os.path.join(os.path.dirname(__file__), '..', 'sample-data')
os.makedirs(OUT, exist_ok=True)

DOCS = ['山田 太郎', '佐藤 健一', '鈴木 一郎', '高橋 誠', '田中 修', '伊藤 直樹']
TS = '2026-11-01T09:00:00.000Z'


def svg_url(svg: str) -> str:
    return 'data:image/svg+xml;base64,' + base64.b64encode(svg.encode('utf-8')).decode()


def angio_svg(label: str, stenosis_at: float) -> str:
    x = 40 + stenosis_at * 220
    return svg_url(f'''<svg xmlns="http://www.w3.org/2000/svg" width="320" height="240" viewBox="0 0 320 240">
<rect width="320" height="240" fill="#1b1b1b"/>
<path d="M30 40 C 90 60, 120 120, 170 140 S 260 200, 300 215" stroke="#bfbfbf" stroke-width="10" fill="none" stroke-linecap="round"/>
<path d="M120 105 C 150 80, 200 70, 280 60" stroke="#a8a8a8" stroke-width="6" fill="none" stroke-linecap="round"/>
<path d="M170 140 C 175 170, 160 200, 150 230" stroke="#9a9a9a" stroke-width="5" fill="none" stroke-linecap="round"/>
<circle cx="{x:.0f}" cy="{40 + stenosis_at * 160:.0f}" r="14" fill="none" stroke="#ffcc00" stroke-width="2" stroke-dasharray="4 3"/>
<text x="10" y="232" fill="#e0e0e0" font-family="sans-serif" font-size="12">{label}</text></svg>''')


def ecg_svg(label: str, st: bool) -> str:
    pts, x = [], 0
    while x < 320:
        base = 120
        pts += [(x, base), (x + 10, base), (x + 14, base - 8), (x + 18, base), (x + 24, base),
                (x + 27, base + 10), (x + 30, base - 60), (x + 33, base + 18), (x + 36, base - (14 if st else 0)),
                (x + 46, base - (16 if st else 4)), (x + 54, base - 12), (x + 60, base)]
        x += 64
    d = 'M' + ' L'.join(f'{a},{b}' for a, b in pts)
    grid = ''.join(f'<line x1="{i}" y1="0" x2="{i}" y2="240" stroke="#f3c6c6" stroke-width="0.5"/>' for i in range(0, 320, 16))
    grid += ''.join(f'<line x1="0" y1="{i}" x2="320" y2="{i}" stroke="#f3c6c6" stroke-width="0.5"/>' for i in range(0, 240, 16))
    return svg_url(f'<svg xmlns="http://www.w3.org/2000/svg" width="320" height="240"><rect width="320" height="240" fill="#fff8f8"/>{grid}'
                   f'<path d="{d}" stroke="#222" stroke-width="1.6" fill="none"/>'
                   f'<text x="8" y="230" font-family="sans-serif" font-size="12" fill="#900">{label}</text></svg>')


def ivus_svg(label: str) -> str:
    return svg_url(f'''<svg xmlns="http://www.w3.org/2000/svg" width="320" height="240"><rect width="320" height="240" fill="#000"/>
<circle cx="160" cy="115" r="92" fill="#3a3a3a"/><ellipse cx="170" cy="112" rx="70" ry="62" fill="#777"/>
<ellipse cx="150" cy="118" rx="34" ry="30" fill="#0a0a0a" stroke="#ddd" stroke-width="2"/>
<path d="M210 80 A 60 55 0 0 1 225 140" stroke="#fff" stroke-width="6" fill="none"/>
<circle cx="150" cy="118" r="5" fill="#ccc"/><text x="8" y="230" font-family="sans-serif" font-size="12" fill="#ddd">{label}</text></svg>''')


def xp_svg(label: str) -> str:
    return svg_url(f'''<svg xmlns="http://www.w3.org/2000/svg" width="320" height="240"><rect width="320" height="240" fill="#111"/>
<ellipse cx="105" cy="120" rx="62" ry="95" fill="#2b2b2b"/><ellipse cx="215" cy="120" rx="62" ry="95" fill="#2b2b2b"/>
<ellipse cx="185" cy="150" rx="70" ry="52" fill="#bdbdbd" opacity="0.8"/><rect x="152" y="10" width="16" height="110" fill="#9e9e9e"/>
<text x="8" y="230" font-family="sans-serif" font-size="12" fill="#ddd">{label}</text></svg>''')


patients = []
PT = [
    ('0001234567', '心臓 一郎', 'シンゾウ イチロウ', 'M', '1952-04-12', 'A', '+'),
    ('0001234568', '冠 花子', 'カンムリ ハナコ', 'F', '1948-09-30', 'O', '+'),
    ('0001234569', '大動 脈男', 'オオドウ ミャクオ', 'M', '1960-01-05', 'B', '+'),
    ('0001234570', '循環 器子', 'ジュンカン キコ', 'F', '1971-06-18', 'AB', '+'),
    ('0001234571', '狭心 太郎', 'キョウシン タロウ', 'M', '1945-12-24', 'A', '+'),
    ('0001234572', '梗塞 次郎', 'コウソク ジロウ', 'M', '1966-03-03', 'O', '+'),
    ('0001234573', '弁膜 和子', 'ベンマク カズコ', 'F', '1939-08-08', 'A', '-'),
    ('0001234574', '血管 健', 'ケッカン ケン', 'M', '1958-11-11', 'B', '+'),
]
for i, (pid, name, kana, sex, birth, bt, rh) in enumerate(PT):
    patients.append({
        'id': f'pt-{i + 1:03d}', 'patientId': pid, 'name': name, 'kana': kana, 'sex': sex, 'birthDate': birth,
        'bloodType': bt, 'rh': rh, 'zip': f'100-00{i:02d}', 'address': f'東京都千代田区架空町{i + 1}-{i + 2}-{i + 3}',
        'phone': f'03-0000-{1000 + i}', 'mobile': f'090-0000-{2000 + i}',
        'emergency': {'name': '家族 代表', 'relation': ['妻', '夫', '長男', '長女'][i % 4], 'phone': f'080-0000-{3000 + i}'},
        'insurance': {'type': ['社保', '国保', '後期高齢'][i % 3], 'number': f'{12345670 + i}'},
        'allergy': {'contrast': i == 2, 'contrastDetail': '蕁麻疹(2019)' if i == 2 else '', 'drug': i == 4,
                    'drugDetail': 'ペニシリン' if i == 4 else '', 'latex': False, 'iodine': i == 2, 'food': ''},
        'infection': {'hbs': '-', 'hcv': '+' if i == 6 else '-', 'hiv': '-', 'syphilis': '-', 'mrsa': '-'},
        'primaryDoctor': DOCS[i % 6], 'ward': ['5東', '6西', 'CCU'][i % 3],
        'referral': {'hospital': ['市民病院', '中央クリニック', '山の手内科', '港北循環器クリニック'][i % 4], 'doctor': '紹介 医師'},
        'dnar': i == 6, 'pastHistory': ['高血圧症、脂質異常症', '2型糖尿病', '慢性腎臓病(G3b)', '特記事項なし'][i % 4],
        'familyHistory': '父：心筋梗塞' if i % 2 == 0 else '', 'medicationNote': 'アスピリン100mg 1T1x' if i % 3 == 0 else '',
        'notes': '', 'createdAt': TS, 'updatedAt': TS,
        'admissions': [{'admitDate': f'2026-0{(i % 8) + 1}-10', 'dischargeDate': f'2026-0{(i % 8) + 1}-17', 'doctor': DOCS[i % 6],
                        'diagnosis': ['労作性狭心症', '急性心筋梗塞', '心不全', '不安定狭心症'][i % 4], 'summary': 'PCI施行後経過良好にて退院。'}],
    })

masters = {
    'doctors': DOCS,
    'hospitals': ['市民病院', '中央クリニック', '山の手内科', '港北循環器クリニック'],
    'devices': [{'category': c, 'name': n} for c, n in [
        ('DES', 'Xience Skypoint'), ('DES', 'Synergy XD'), ('DES', 'Resolute Onyx'), ('DES', 'Ultimaster Nagomi'), ('DES', 'Orsiro Mission'),
        ('Balloon', 'Ryurei'), ('Balloon', 'Emerge'), ('NC Balloon', 'NC Trek'), ('NC Balloon', 'Hiryu'), ('Scoring', 'Scoreflex'),
        ('Cutting', 'Wolverine'), ('DCB', 'SeQuent Please'), ('DCB', 'Agent'), ('Rota burr', 'Rotablator'), ('IVL', 'Shockwave C2+'),
        ('Aspiration', 'Thrombuster III'), ('Filter', 'Filtrap'), ('Guiding', 'Launcher'), ('Guiding', 'Heartrail'),
        ('Micro', 'Corsair Pro'), ('Micro', 'Caravel'), ('Micro', 'Finecross'), ('GW', 'Sion blue'), ('GW', 'Runthrough NS'),
        ('GW', 'Gaia Next 1'), ('GW', 'Fielder XT-A'), ('GW', 'Ultimate Bros 3')]],
}


def segs(findings):
    base = {}
    for k in ['RCA1', 'RCA2', 'RCA3', 'RCA4AV', 'RCA4PD', 'LMT5', 'LAD6', 'LAD7', 'LAD8', 'LAD9', 'LAD10', 'LCX11', 'HL', 'LCX12', 'LCX13', 'LCX14', 'LCX15']:
        base[k] = {'size': 'Large' if k in ('RCA1', 'LMT5', 'LAD6', 'LCX11') else '', 'stenosis': 'Normal'}
    for k, v in findings.items():
        base[k].update(v)
    return base


def cath_record(urgency, purposes, items, disease, op, att, extra=None):
    r = {
        'exam': {'urgency': urgency, 'totalCathCount': str(random.randint(1, 4)), 'purposes': purposes, 'examItems': items,
                 'disease': disease, 'diagnosis': disease, 'treatmentPolicy': 'PCI予定' if 'PCI' not in items else '内服加療継続',
                 'approach': 'Rt Radial', 'sheath': {'name': 'Glidesheath Slender', 'size': '6'},
                 'contrast': {'agent': 'イオパミロン370', 'volume': str(random.randint(60, 220))},
                 'fluoroTime': str(random.randint(5, 45)), 'totalDose': str(random.randint(300, 2500)),
                 'flags': {'ccuHotline': urgency == '緊急'}},
        'doctors': {'attending': att, 'outpatient': att, 'operators': [op, DOCS[(DOCS.index(op) + 1) % 6], ''],
                    'assistants': [DOCS[(DOCS.index(op) + 2) % 6], '', ''], 'referralHospital': '市民病院', 'referralDoctor': '紹介 医師'},
        'hemo': {'pressures': {'Ao': {'s': str(random.randint(110, 160)), 'd': str(random.randint(60, 90)), 'm': str(random.randint(80, 110))},
                               'LV': {'s': str(random.randint(110, 160)), 'd': '5', 'm': ''},
                               'LVpost': {'s': str(random.randint(110, 160)), 'd': str(random.randint(8, 22)), 'm': ''}},
                 'values': {'HR': str(random.randint(58, 92))}},
        'body': {'height': str(random.randint(150, 178)), 'weight': str(random.randint(48, 86)), 'bodyTemp': '36.5'},
        'labs': {'admission': {'AST': str(random.randint(15, 60)), 'ALT': str(random.randint(10, 50)), 'LDH': str(random.randint(150, 400)),
                               'Cr': f'{random.uniform(0.6, 2.2):.2f}', 'GFR': str(random.randint(25, 90)), 'Na': '140', 'K': f'{random.uniform(3.6, 5.2):.1f}',
                               'CRP': f'{random.uniform(0.02, 2.5):.2f}', 'BNP': str(random.randint(10, 600)), 'HbA1c': f'{random.uniform(5.2, 8.4):.1f}',
                               'LDL': str(random.randint(60, 160)), 'HDL': str(random.randint(30, 70)), 'TG': str(random.randint(70, 250))},
                 'cbc': {'WBC': str(random.randint(4000, 12000)), 'Hb': f'{random.uniform(9.5, 15.5):.1f}', 'Plt': f'{random.uniform(12, 30):.1f}'},
                 'hbs': {'date': '2026-10-01', 'hbsAg': '(-)', 'hbsAgC': '0.01'}, 'hcv': {'date': '2026-10-01', 'hcvAb': '(-)', 'hcvAbC': '0.1'}},
        'risk': {'DM': random.choice(['-', '+']), 'HT': '+', 'HL': random.choice(['-', '+']), 'HD': '-', 'CAPD': '-', 'family': random.choice(['-', '+']),
                 'smoking': random.choice(['-', 'past', '+']), 'smokingPerDay': '20', 'smokingStartAge': '20', 'smokingQuitAge': '60'},
        'pciSummary': '', 'futurePlan': 'DAPT継続、1年後フォローアップCAG予定', 'comment': '',
    }
    if extra:
        for k, v in extra.items():
            r.setdefault(k, {}).update(v) if isinstance(v, dict) else r.__setitem__(k, v)
    return r


def lesion(target, sub, tech, pre, post, devices, success='Success', morph=None, timi=('3', '3')):
    return {
        'target': target, 'targetSub': sub, 'success': success, 'type': random.choice(['B1', 'B2', 'C']), 'deNovoMajor': 'de novo', 'deNovoMinor': 'focal',
        'morph': {'eccentricity': 'yes', 'calcification': random.choice(['yes', 'no']), 'bifurcation': 'no', 'irregular': 'no', 'thrombus': 'no',
                  'cto': 'no', 'dissection': 'no', 'haziness': 'no', 'ostial': 'no', **(morph or {})},
        'angulation': '<45°', 'proximalTortuosity': 'None', 'lengthA': str(random.randint(10, 30)), 'lengthB': '',
        'pre': {'ref': '3.0', 'pct': pre, 'mld': '0.6'}, 'post': {'ref': '3.1', 'pct': post, 'mld': '2.8'},
        'technique': 'Direct stenting' if 'STENT' in tech else 'POBA', 'stentingReason': 'de novo lesion', 'stentingMethod': 'IVUS guided',
        'device': {'morphPost': 'Good expansion', 'items': devices, 'result': 'Success', 'desHybrid': 'no', 'desBmsHybrid': 'no',
                   'final': {'balloon': '3.25', 'stentLen': str(sum(int(d.get('length') or 0) for d in devices)), 'maxPress': '18'}},
        'summary': {'treatment': '+'.join(tech), 'tech': {t: True for t in tech}, 'pre': pre, 'post': post, 'timiPre': timi[0], 'timiPost': timi[1], 'rentrop': '0'},
        'comp': {'perforation': 'no', 'slowNoFlow': 'no'},
    }


def dev(cat, name, size, length, pres):
    return {'category': cat, 'name': name, 'size': size, 'length': length, 'pressure': pres}


reports = []


def report(i, pidx, date, cine, pci_no, status, verified, cr, cag=None, pci=None, pi=None, pcps=None, conf=None, mace=None, images=None, header=None):
    r = {'id': f'rp-{i:03d}', 'patientRef': f'pt-{pidx:03d}', 'status': status, 'verified': verified,
         'header': {'studyDate': date, 'cineNo': cine, 'pciNo': pci_no, 'accessionNo': f'ACC{20260000 + i}', 'secretaryChecked': verified,
                    'summary': conf is not None, 'submitted': False, 'qca': pci is not None, 'registrant': cr['doctors']['operators'][0], **(header or {})},
         'cathRecord': cr, 'createdAt': f'{date}T10:00:00.000Z', 'updatedAt': f'{date}T15:00:00.000Z',
         'history': [{'at': f'{date}T10:00:00.000Z', 'by': cr['doctors']['operators'][0], 'action': '新規作成'},
                     {'at': f'{date}T15:00:00.000Z', 'by': cr['doctors']['operators'][0], 'action': '保存（カテ記録）'}]}
    if cag: r['cagLvg'] = cag
    if pci: r['pci'] = pci
    if pi: r['pressureIvus'] = pi
    if pcps: r['pcps'] = pcps
    if conf: r['conference'] = conf
    if mace: r['mace'] = mace
    if images: r['images'] = images
    reports.append(r)


def cag_block(findings, comment, lesions, syntax, lvg_ef=None, collaterals=None, grafts=None):
    c = {'approach': {'artery': 'Rt Radial', 'arterySheath': {'name': 'Glidesheath Slender', 'size': '6'}, 'vein': '', 'veinSheath': {'name': '', 'size': ''}, 'support': ''},
         'catheters': {'LCA': {'label': '', 'shape': 'JL3.5', 'size': '5'}, 'RCA': {'label': '', 'shape': 'JR4', 'size': '5'}, 'LV': {'label': '', 'shape': 'Pigtail', 'size': '5'}},
         'cag': {'dominance': 'Right', 'segments': segs(findings), 'comment': comment, 'lesions': lesions, 'syntax': syntax, 'euro': '1.8', 'japan': '1.2',
                 'squeezing': '-', 'spasm': '-'}}
    if collaterals:
        c['cag']['collaterals'] = collaterals
    if grafts:
        c['cag']['grafts'] = grafts
    if lvg_ef:
        edv, esv = 120, int(120 * (1 - lvg_ef / 100))
        c['lvg'] = {'performed': True, 'view': 'RAO30/LAO60', 'agent': 'イオパミロン370', 'volume': '30', 'rate': '10',
                    'values': {'LVEDV': str(edv), 'LVESV': str(esv), 'LVSV': str(edv - esv), 'EF': str(lvg_ef), 'LVEDP': '14', 'HR': '72'},
                    'wallMotion': {'1': 'N', '2': 'Hypo' if lvg_ef < 50 else 'N', '3': 'A' if lvg_ef < 40 else 'N', '4': 'N', '5': 'N', '6': 'N', '7': 'N'},
                    'mr': 'I', 'comment': f'EF {lvg_ef}%'}
    return c


# 1: 安定狭心症 LAD PCI（確定）
cr = cath_record('待機', {'CAG': True, 'PCI': True}, 'CAG,PCI,IVUS', 'AP', DOCS[0], DOCS[0])
cr['pciSummary'] = 'LAD#7 90% → DES 3.0x28mm 留置。0%で終了。'
report(1, 1, '2026-11-02', 'C26-1101', 'P26-301', '入力中', True, cr,
       cag=cag_block({'LAD7': {'stenosis': '90', 'calc': True, 'jeopardy': True}, 'RCA2': {'stenosis': '50'}}, 'LAD#7 90% 狭窄。RCA#2 50%。', {'count': '1', 'LAD': True}, '12', 62),
       pci={'basic': {'lesionCount': '1', 'result': 'Success', 'guiding': [{'name': 'Launcher EBU3.5', 'size': '6'}], 'micro': [''], 'gw': ['Sion blue', 'Runthrough NS']},
            'lesions': [lesion('#7', 'LAD', ['STENT'], '90', '0', [dev('NC Balloon', 'NC Trek', '2.5', '12', '14'), dev('DES', 'Xience Skypoint', '3.0', '28', '16'), dev('NC Balloon', 'Hiryu', '3.25', '12', '18')])],
            'jpci': {'bg': {'pciHx': 'no', 'cabgHx': 'no', 'priorMI': 'no', 'priorHF': 'no', 'symptom1m': '安定狭心症', 'admitDx': '安定冠動脈疾患', 'lesionCount': '1', 'lmt': 'no'},
                     'pre': {'antiplatelet': 'yes', 'apItems': {'aspirin': True, 'prasugrel': True}, 'anticoag': 'no', 'imaging': 'yes', 'imagingItems': {'ct': True}},
                     'info': {'jpciOperator': DOCS[0], 'firstOp': DOCS[0], 'firstOpNo': 'J-10001', 'status': '待機', 'accessSite': '橈骨動脈', 'procComp': 'no',
                              'mcs': 'no', 'imaging': 'yes', 'imagingItems': {'IVUS': True}},
                     'post': {'antithrombotic': {'aspirin': True, 'prasugrel': True}, 'lipid': {'statinHigh': True}}, 'discharge': {'pciResult': '成功'}},
            'risk': {'hbrMinor': {'age75': False}, 'credo': {'dm': True}, 'daptMonths': '3'}},
       pi={'lesions': [{'site': 'LAD#7', 'pre': {'minLD': {'lesion': '1.4', 'proximal': '3.0', 'distal': '2.6'}, 'lumenCSA': {'lesion': '1.9', 'proximal': '7.2', 'distal': '5.4'},
                                                'vesselCSA': {'lesion': '11.8', 'proximal': '13.0', 'distal': '9.9'}},
                        'post': {'minLD': {'lesion': '2.8', 'proximal': '3.1', 'distal': '2.7'}, 'lumenCSA': {'lesion': '6.6', 'proximal': '7.5', 'distal': '5.8'},
                                 'vesselCSA': {'lesion': '12.0', 'proximal': '13.1', 'distal': '10.0'}}, 'fibrous': True, 'calcification': True, 'calcDegree': '90', 'device': 'OptiCross'}]},
       conf={'wardDoctor': DOCS[0], 'disease': 'AP', 'nyha': 'I', 'ccs': 'II', 'onsetCourse': '2026年9月より労作時胸部圧迫感。冠動脈CTでLAD高度狭窄疑いにて精査加療目的入院。',
             'ucg': {'date': '2026-10-20', 'LVDd': '48', 'LVDs': '32', 'EF': '62', 'wallMotion': '前壁軽度hypo'}},
       mace=[{'mace': '0', 'pciDate': '2026-11-02', 'lastVisit': '2026-11-16', 'negative': {'checked': True, 'date': '2026-11-16'}}],
       images=[{'id': 'img-001', 'category': 'Cine', 'takenAt': '2026-11-02', 'view': 'RAO30/CRA30', 'lesion': 'LAD#7', 'title': 'Pre PCI LAD',
                'description': 'LAD#7 90%狭窄', 'fileName': 'lad_pre.svg', 'mimeType': 'image/svg+xml', 'dataUrl': angio_svg('Pre PCI  RAO30/CRA30', 0.55), 'keyImage': True},
               {'id': 'img-002', 'category': 'Cine', 'takenAt': '2026-11-02', 'view': 'RAO30/CRA30', 'lesion': 'LAD#7', 'title': 'Final',
                'description': 'DES留置後 0%', 'fileName': 'lad_final.svg', 'mimeType': 'image/svg+xml', 'dataUrl': angio_svg('Final  RAO30/CRA30', 0.55), 'keyImage': False},
               {'id': 'img-003', 'category': 'IVUS', 'takenAt': '2026-11-02', 'view': '', 'lesion': 'LAD#7', 'title': 'IVUS MLA部',
                'description': 'MLA 1.9mm², 石灰化90°', 'fileName': 'ivus.svg', 'mimeType': 'image/svg+xml', 'dataUrl': ivus_svg('IVUS  LAD#7 MLA'), 'keyImage': False},
               {'id': 'img-004', 'category': 'ECG', 'takenAt': '2026-11-01', 'view': '', 'lesion': '', 'title': '入院時心電図',
                'description': '洞調律、有意なST変化なし', 'fileName': 'ecg.svg', 'mimeType': 'image/svg+xml', 'dataUrl': ecg_svg('12誘導 II', False), 'keyImage': False}])

# 2: STEMI 緊急PCI（入力中）
cr = cath_record('緊急', {'CAG': True, 'PCI': True}, 'CAG,PCI,IVUS', 'AMI', DOCS[2], DOCS[2])
cr['labs']['admission'].update({'TnT': '2.45', 'CRP': '0.35'})
cr['pciSummary'] = 'RCA#1 100% (TIMI0) → 血栓吸引後 DES 3.5x24mm。TIMI3 で終了。'
report(2, 6, '2026-11-05', 'C26-1102', 'P26-302', '入力中', False, cr,
       cag=cag_block({'RCA1': {'stenosis': '100', 'jeopardy': True}, 'LAD7': {'stenosis': '75'}}, 'RCA#1 完全閉塞（責任病変）。LAD#7 75%。', {'count': '2', 'LAD': True, 'RCA': True}, '22', 48,
                     collaterals=[{'from': 'LAD', 'to': 'RCA4PD', 'grade': '1', 'state': 'Poor'}]),
       pci={'basic': {'lesionCount': '1', 'result': 'Success', 'killip': 'II', 'elapsed': '186'},
            'lesions': [lesion('#1', 'RCA', ['ASP', 'STENT'], '100', '0', [dev('Aspiration', 'Thrombuster III', '6Fr', '', ''), dev('Balloon', 'Ryurei', '2.0', '15', '8'),
                                                                          dev('DES', 'Synergy XD', '3.5', '24', '14')], morph={'thrombus': 'yes'}, timi=('0', '3'))],
            'jpci': {'bg': {'arrest24': 'no', 'shock24': 'no', 'ahf24': 'no', 'symptom1m': 'STEMI', 'admitDx': 'STEMI'}, 'info': {'status': '緊急', 'mcs': 'no', 'procComp': 'no'}},
            'ami': {'onset': {'date': '2026-11-05', 'time': '05:40'}, 'call': {'date': '2026-11-05', 'time': '06:10'}, 'sceneArr': {'date': '2026-11-05', 'time': '06:19'},
                    'sceneDep': {'date': '2026-11-05', 'time': '06:35'}, 'hospArr': {'date': '2026-11-05', 'time': '06:52'}, 'cathLab': {'date': '2026-11-05', 'time': '07:20'},
                    'firstDevice': {'date': '2026-11-05', 'time': '07:46'}},
            'risk': {'credo': {'age75': False, 'dm': True}, 'st': {'acs': True}, 'daptMonths': '12'}},
       images=[{'id': 'img-005', 'category': 'ECG', 'takenAt': '2026-11-05', 'view': '', 'lesion': '', 'title': '来院時心電図', 'description': 'II, III, aVF ST上昇',
                'fileName': 'ecg_stemi.svg', 'mimeType': 'image/svg+xml', 'dataUrl': ecg_svg('II  ST上昇', True), 'keyImage': True},
               {'id': 'img-006', 'category': 'Cine', 'takenAt': '2026-11-05', 'view': 'LAO45', 'lesion': 'RCA#1', 'title': 'RCA 閉塞', 'description': 'RCA#1 TIMI0',
                'fileName': 'rca_occl.svg', 'mimeType': 'image/svg+xml', 'dataUrl': angio_svg('RCA  LAO45', 0.15), 'keyImage': False}])

# 3: CAG + Pressure wire（診断のみ）
cr = cath_record('待機', {'CAG': True}, 'CAG,Pressure study,FFR,iFR', 'SAP', DOCS[1], DOCS[3])
report(3, 2, '2026-11-06', 'C26-1103', '', '入力中', True, cr,
       cag=cag_block({'LCX13': {'stenosis': '75'}, 'LAD6': {'stenosis': '50'}}, 'LCX#13 75%。Pressure wireで評価。', {'count': '0'}, '8', 65),
       pi={'pressure': [{'lesion': 'LCX#13', 'phase': '診断のみ', 'drug': 'ATP', 'dominancy': 'Right', 'priorMI': '-', 'stent': '-',
                         'metrics': {'baselinePdPa': '0.89', 'FFR': '0.78', 'iFR': '0.87', 'RFR': '0.88', 'cfrThermo': '2.1', 'IMR': '22'},
                         'qca': {'pctDS': '62', 'lesionLength': '14.2', 'refDiameter': '2.8', 'mld': '1.06'}},
                        {'lesion': 'LAD#6', 'phase': '診断のみ', 'drug': 'ATP', 'dominancy': 'Right', 'priorMI': '-', 'stent': '-',
                         'metrics': {'baselinePdPa': '0.95', 'FFR': '0.86', 'iFR': '0.94'}, 'qca': {'pctDS': '45'}}]})

# 4: AMI + PCPS（緊急）
cr = cath_record('緊急', {'CAG': True, 'PCI': True}, 'CAG,PCI,PCPS,IABP', 'AMI', DOCS[3], DOCS[3])
cr['prognosis'] = {'deathDate': '', 'confirmDate': '2026-11-15', 'confirmer': DOCS[3], 'comment': 'CCU管理中'}
report(4, 3, '2026-11-08', 'C26-1104', 'P26-303', '入力中', False, cr,
       cag=cag_block({'LMT5': {'stenosis': '99', 'jeopardy': True}, 'LAD6': {'stenosis': '90'}}, 'LMT#5 99%。心原性ショック。', {'count': '3', 'LMT': True, 'LAD': True, 'LCX': True}, '38'),
       pci={'basic': {'lesionCount': '1', 'support': 'PCPS', 'result': 'Success', 'killip': 'IV'},
            'lesions': [lesion('#5', 'LMT', ['LMT', 'STENT'], '99', '10', [dev('DES', 'Resolute Onyx', '4.0', '18', '14'), dev('NC Balloon', 'NC Trek', '4.5', '8', '16')], timi=('2', '3'))],
            'patientTreat': {'IABP': 'yes', 'PCPS': 'yes'},
            'jpci': {'bg': {'arrest24': 'yes', 'shock24': 'yes'}, 'info': {'status': '緊急', 'mcs': 'yes', 'mcsItems': {'PCPS': True, 'IABP': True}, 'mcsTiming': {'PCPS': 'pre', 'IABP': 'intra'}}},
            'ami': {'onset': {'date': '2026-11-08', 'time': '21:05'}, 'hospArr': {'date': '2026-11-08', 'time': '21:58'}, 'cathLab': {'date': '2026-11-08', 'time': '22:20'},
                    'firstDevice': {'date': '2026-11-08', 'time': '22:51'}}},
       pcps={'arrest': {'date': '2026-11-08', 'time': '21:15'}, 'call': {'date': '2026-11-08', 'time': '21:16'}, 'sceneArr': {'date': '2026-11-08', 'time': '21:24'},
             'sceneDep': {'date': '2026-11-08', 'time': '21:38'}, 'hospArr': {'date': '2026-11-08', 'time': '21:58'}, 'cathLab': {'date': '2026-11-08', 'time': '22:20'},
             'start': {'date': '2026-11-08', 'time': '22:32'}, 'firstEcg': 'VF', 'operators': [DOCS[3], DOCS[4], ''], 'primingOperator': '臨床工学技士 A', 'rosc': '22:40',
             'detail': {'inflowSite': 'Rt FA', 'inflowSize': '16.5Fr', 'outflowSite': 'Rt FV', 'outflowSize': '21Fr', 'initialFlow': '3.2', 'outcome': '離脱予定'}},
       images=[{'id': 'img-007', 'category': 'X-P', 'takenAt': '2026-11-09', 'view': 'AP', 'lesion': '', 'title': '胸部X線 (PCPS留置後)',
                'description': '肺うっ血あり', 'fileName': 'xp.svg', 'mimeType': 'image/svg+xml', 'dataUrl': xp_svg('Chest AP'), 'keyImage': False}])

# 5: CTO PCI
cr = cath_record('待機', {'CAG': True, 'PCI': True}, 'CAG,PCI,IVUS', 'OMI', DOCS[0], DOCS[4])
report(5, 5, '2026-11-10', 'C26-1105', 'P26-304', '入力中', True, cr,
       cag=cag_block({'RCA2': {'stenosis': '100', 'graftable': True}}, 'RCA#2 CTO（J-CTO 2）。LADからのCollateral Rentrop 2。', {'count': '1', 'RCA': True}, '15', 55,
                     collaterals=[{'from': 'LAD septal', 'to': 'RCA4PD', 'grade': '2', 'state': 'Good'}, {'from': 'LCX', 'to': 'RCA4AV', 'grade': '1', 'state': 'Poor'}]),
       pci={'basic': {'lesionCount': '1', 'result': 'Success', 'gw': ['Fielder XT-A', 'Gaia Next 1', 'Ultimate Bros 3'], 'micro': ['Corsair Pro', 'Caravel']},
            'lesions': [{**lesion('#2', 'RCA', ['STENT'], '100', '0', [dev('Balloon', 'Ryurei', '1.25', '10', '12'), dev('DES', 'Ultimaster Nagomi', '3.0', '38', '14'),
                                                                        dev('DES', 'Ultimaster Nagomi', '3.5', '24', '14')], morph={'cto': 'yes'}, timi=('0', '3')),
                         'ageOfOcclusion': '>3ヶ月',
                         'cto': {'access': 'Retrograde', 'gwMethod': 'Reverse CART', 'parallelWire': 'yes',
                                 'retro': {'access': 'Septal', 'gc': {'name': 'EBU3.5', 'size': '7'}, 'gw': 'Sion', 'vessel': 'LAD', 'channel': 'Septal CC', 'channelWire': 'Sion'}}}],
            'ctoScore': '2'})

# 6: CABG後グラフト評価
cr = cath_record('待機', {'CAG': True, 'followUp': True}, 'CAG,LVG', 'SAP', DOCS[4], DOCS[1])
cr['exam']['followUpReason'] = 'CABG後1年'
report(6, 4, '2026-11-11', 'C26-1106', '', '入力中', False, cr,
       cag=cag_block({'LAD6': {'stenosis': '100'}, 'LCX13': {'stenosis': '90'}}, 'Native LAD/LCX閉塞。LITA-LAD patent、SVG-OM patent。', {'count': '0'}, '', 58,
                     grafts=[{'graft': 'LITA', 'anastomosis': 'LAD#8', 'patency': 'Patent'}, {'graft': 'SVG', 'anastomosis': 'OM(#12)', 'patency': 'Patent'}]))

# 7: 弁膜症 右心カテ
cr = cath_record('待機', {'CAG': True, 'SG': True}, 'CAG,RHC', 'AS', DOCS[5], DOCS[5])
cr['hemo']['pressures'].update({'RA': {'s': '', 'd': '', 'm': '8'}, 'RV': {'s': '42', 'd': '6', 'm': ''}, 'PA': {'s': '40', 'd': '18', 'm': '27'}, 'PCW': {'s': '', 'd': '', 'm': '18'}})
cr['hemo']['values'].update({'CO': '3.9', 'CI': '2.6', 'AVG': '48', 'AVA': '0.72'})
report(7, 7, '2026-11-12', 'C26-1107', '', '確定', True, cr,
       cag=cag_block({'LAD6': {'stenosis': 'Irregular'}}, '有意狭窄なし。重症AS（AVA 0.72cm²）。', {'count': '0'}, '0'))

# 8: EVT
cr = cath_record('待機', {'EVT': True}, 'EVT', 'LEAD', DOCS[1], DOCS[1])
report(8, 8, '2026-11-13', 'C26-1108', '', '入力中', False, cr)

# 9: 新規（入力途中）
cr = cath_record('緊急', {'CAG': True}, 'CAG', 'u-AP', DOCS[2], DOCS[0])
report(9, 1, '2026-11-17', 'C26-1109', '', '入力中', False, cr,
       cag=cag_block({'LAD7': {'stenosis': '25'}, 'RCA2': {'stenosis': '50'}}, 'ステント内再狭窄なし。', {'count': '0'}, '6'))


# ---------------------------------------------------------------- サンプル画像（tools/sample_images.py）
import sys as _sys
_sys.path.insert(0, os.path.dirname(__file__))
import sample_images as SI

_img_seq = [0]


def img(cat, date, title, desc, data, view='', lesion='', key=False):
    _img_seq[0] += 1
    return {'id': f'img-{_img_seq[0]:03d}', 'category': cat, 'takenAt': date, 'view': view, 'lesion': lesion, 'title': title, 'description': desc,
            'fileName': f'sample_{_img_seq[0]:03d}.svg', 'mimeType': 'image/svg+xml', 'dataUrl': data, 'keyImage': key}


IMAGES = {
    'rp-001': [  # 安定狭心症 LAD PCI
        img('ECG', '2026-11-01', '入院時 12誘導心電図', '洞調律。有意なST変化なし。', SI.ecg12('12誘導 入院時')),
        img('CT', '2026-10-20', '冠動脈CT（LAD）', 'LAD#7 に石灰化を伴う高度狭窄疑い。', SI.ccta('CCTA LAD CPR', 0.45), 'CPR', 'LAD#7'),
        img('Cine', '2026-11-02', 'LCA Pre', 'LAD#7 90% 狭窄。', SI.angio('LCA  RAO30/CRA30  Pre', 'LCA', [('LAD', 0.35, 0.8)], seed=2), 'RAO30/CRA30', 'LAD#7', True),
        img('Cine', '2026-11-02', 'LCA Pre（LAO）', 'LAD#7 狭窄、LCX 有意狭窄なし。', SI.angio('LCA  LAO45/CRA25  Pre', 'LCA', [('LAD', 0.4, 0.8)], seed=3), 'LAO45/CRA25', 'LAD#7'),
        img('IVUS', '2026-11-02', 'IVUS Pre（MLA部）', 'MLA 1.9mm²、石灰化 90°。', SI.ivus('IVUS LAD#7 MLA', 230, 90), '', 'LAD#7'),
        img('Cine', '2026-11-02', 'LCA Final', 'DES 3.0×28mm 留置後 0%。', SI.angio('LCA  RAO30/CRA30  Final', 'LCA', [], stent=('LAD', 0.25, 0.5), seed=4), 'RAO30/CRA30', 'LAD#7', True),
        img('IVUS', '2026-11-02', 'IVUS Post（ステント内）', 'MSA 6.6mm²、良好な拡張。', SI.ivus('IVUS LAD#7 Post', 120, 90, stent=True), '', 'LAD#7'),
        img('Cine', '2026-11-02', 'LVG 拡張末期', 'EF 62%。壁運動正常。', SI.lvg('LVG RAO30 拡張末期', 'diastole', 62), 'RAO30'),
        img('Cine', '2026-11-02', 'LVG 収縮末期', '', SI.lvg('LVG RAO30 収縮末期', 'systole', 62), 'RAO30'),
    ],
    'rp-002': [  # STEMI RCA
        img('ECG', '2026-11-05', '来院時 12誘導心電図', 'II・III・aVF ST上昇、I・aVL 対側性ST低下。', SI.ecg12('12誘導 来院時（下壁STEMI）', ('II', 'III', 'aVF')), key=True),
        img('Cine', '2026-11-05', 'RCA 閉塞', 'RCA#1 完全閉塞（TIMI 0）。', SI.angio('RCA  LAO45  Pre', 'RCA', [], occluded=('main', 0.2), seed=6), 'LAO45', 'RCA#1', True),
        img('Cine', '2026-11-05', 'LCA', 'LAD#7 75%。RCA への側副血行路（Rentrop 1）。', SI.angio('LCA  RAO30/CAU25', 'LCA', [('LAD', 0.4, 0.6)], seed=7, collateral=True), 'RAO30/CAU25', 'LAD#7'),
        img('Cine', '2026-11-05', 'RCA 血栓吸引後', '再灌流 TIMI 2、#1 に残存狭窄・血栓像。', SI.angio('RCA  LAO45  吸引後', 'RCA', [('main', 0.18, 0.75)], seed=8), 'LAO45', 'RCA#1'),
        img('Cine', '2026-11-05', 'RCA Final', 'DES 3.5×24mm 留置、TIMI 3。', SI.angio('RCA  LAO45  Final', 'RCA', [], stent=('main', 0.1, 0.3), seed=9), 'LAO45', 'RCA#1', True),
        img('ECG', '2026-11-06', 'PCI 翌日 12誘導心電図', 'ST 上昇は改善傾向、III・aVF に異常Q波。', SI.ecg12('12誘導 PCI翌日')),
    ],
    'rp-003': [  # Pressure wire
        img('Cine', '2026-11-06', 'LCA', 'LCX#13 75%、LAD#6 50%。', SI.angio('LCA  RAO30/CAU25', 'LCA', [('LCX', 0.6, 0.65), ('LAD', 0.15, 0.4)], seed=10), 'RAO30/CAU25', 'LCX#13', True),
        img('Other', '2026-11-06', 'Pressure wire LCX#13', 'FFR 0.78（ATP 静注）、iFR 0.87。', SI.pressure_trace('Pressure wire  LCX#13', 0.78, 0.87), '', 'LCX#13', True),
        img('Other', '2026-11-06', 'Pressure wire LAD#6', 'FFR 0.86、iFR 0.94（虚血陰性）。', SI.pressure_trace('Pressure wire  LAD#6', 0.86, 0.94), '', 'LAD#6'),
        img('Scinti', '2026-10-25', '負荷心筋シンチ', '側壁に可逆性灌流欠損。', SI.scinti('Stress Tc  polar map', ('lateral',))),
    ],
    'rp-004': [  # LMT + PCPS
        img('ECG', '2026-11-08', '心停止時 心電図', '心室細動。', SI.ecg12('モニター心電図 VF', rhythm='vf'), key=True),
        img('Cine', '2026-11-08', 'LCA（LMT）', 'LMT#5 99% 狭窄。', SI.angio('LCA  AP/CAU  Pre', 'LCA', [('main', 0.6, 0.9)], seed=12), 'AP/CRA30', 'LMT#5', True),
        img('Cine', '2026-11-08', 'LCA Final', 'LMT〜LAD に DES 4.0×18mm。', SI.angio('LCA  AP/CAU  Final', 'LCA', [], stent=('main', 0.3, 1.0), seed=13), 'AP/CRA30', 'LMT#5'),
        img('X-P', '2026-11-09', '胸部X線（PCPS・IABP留置後）', '肺うっ血あり。送脱血管・IABP 先端位置良好。', SI.chest_xp('Chest AP  PCPS/IABP', congestion=True, devices=True), 'AP'),
        img('UCG', '2026-11-09', '心エコー', '前壁中隔〜心尖部 akinesis、EF 25%。', SI.ucg('UCG', 'PLAX', 'EF 25%')),
    ],
    'rp-005': [  # CTO
        img('Cine', '2026-11-10', '両側造影', 'RCA#2 CTO、LAD septal からの側副血行路（Rentrop 2）。', SI.angio('Bilateral  LAO45', 'RCA', [], occluded=('main', 0.35), seed=14, collateral=True), 'LAO45', 'RCA#2', True),
        img('Cine', '2026-11-10', 'Reverse CART 後', 'Retrograde wire 通過。', SI.angio('RCA  LAO45  Retrograde', 'RCA', [('main', 0.38, 0.7)], seed=15), 'LAO45', 'RCA#2'),
        img('IVUS', '2026-11-10', 'IVUS（CTO 内）', '偽腔なく真腔を確認。', SI.ivus('IVUS RCA#2', 300, 0), '', 'RCA#2'),
        img('Cine', '2026-11-10', 'RCA Final', 'DES 3.0×38mm＋3.5×24mm 留置、TIMI 3。', SI.angio('RCA  LAO45  Final', 'RCA', [], stent=('main', 0.2, 0.55), seed=16), 'LAO45', 'RCA#2', True),
    ],
    'rp-006': [  # CABG 後
        img('Cine', '2026-11-11', 'Native LCA', 'LAD#6・LCX#13 閉塞。', SI.angio('LCA  RAO30', 'LCA', [], occluded=('LAD', 0.15), seed=17), 'RAO30', 'LAD#6'),
        img('Cine', '2026-11-11', 'LITA-LAD グラフト', 'LITA patent、吻合部良好。', SI.angio('LITA  LAT', 'SFA', [], seed=18), 'Lateral', 'LAD#8', True),
        img('CT', '2026-10-30', 'グラフト CT', 'LITA・SVG とも開存。', SI.ccta('CCTA Graft', 0.7, calc=False), 'CPR'),
    ],
    'rp-007': [  # AS
        img('UCG', '2026-11-01', '心エコー（AS）', 'AVA 0.7cm²、Vmax 4.6m/s、平均圧較差 52mmHg。', SI.ucg('UCG', 'PLAX', 'AVA 0.7cm²'), key=True),
        img('Other', '2026-11-12', 'LV-Ao 同時圧', '平均圧較差 48mmHg。', SI.pressure_trace('LV / Ao simultaneous', 0.62), ''),
        img('Cine', '2026-11-12', 'LCA', '有意狭窄なし。', SI.angio('LCA  RAO30/CAU25', 'LCA', [], seed=19), 'RAO30/CAU25'),
    ],
    'rp-008': [  # EVT
        img('Cine', '2026-11-13', '右浅大腿動脈 Pre', 'SFA 中部 99% 狭窄。', SI.angio('Rt SFA  Pre', 'SFA', [('main', 0.55, 0.9)], seed=20), 'AP', 'SFA', True),
        img('Cine', '2026-11-13', '右浅大腿動脈 Final', 'ステント留置後良好。', SI.angio('Rt SFA  Final', 'SFA', [], stent=('main', 0.45, 0.65), seed=21), 'AP', 'SFA'),
    ],
    'rp-009': [
        img('Cine', '2026-11-17', 'LCA（フォローアップ）', 'LAD ステント内再狭窄なし。', SI.angio('LCA  RAO30/CRA30', 'LCA', [('LAD', 0.4, 0.3)], stent=('LAD', 0.25, 0.5), seed=22), 'RAO30/CRA30', 'LAD#7', True),
        img('ECG', '2026-11-17', '12誘導心電図', '洞調律。', SI.ecg12('12誘導')),
    ],
}
for r in reports:
    if r['id'] in IMAGES:
        r['images'] = IMAGES[r['id']]

# ---- 優先度「高」の項目（G-01・G-08・G-25・G-35）
MOVED_HISTORY = ['priorMI', 'priorHF', 'pciHx', 'cabgHx', 'renal', 'copd', 'pad']  # J-PCI → カテ記録
TIMES = {'rp-001': ('09:05', '10:20'), 'rp-002': ('22:40', '23:55'), 'rp-003': ('13:10', '13:50'), 'rp-004': ('03:15', '05:05'),
         'rp-005': ('09:00', '12:10'), 'rp-006': ('14:00', '14:45'), 'rp-007': ('10:30', '11:05'), 'rp-008': ('13:30', '15:00'),
         'rp-009': ('09:30', '10:05')}
for r in reports:
    cr_ = r.setdefault('cathRecord', {})
    bg = r.get('pci', {}).get('jpci', {}).get('bg', {})
    risk = cr_.setdefault('risk', {})
    for k in MOVED_HISTORY:
        if k in bg:
            risk.setdefault(k, bg.pop(k))
    st, en = TIMES.get(r['id'], ('', ''))
    cr_.setdefault('exam', {}).update({'startTime': st, 'endTime': en})
    cr_['complications'] = {'status': 'no', 'items': {}, 'detail': ''}
    # ACC/AHA Type を形態と合わせる（rp-002：病変長 30mm、rp-005：3か月以上の CTO → Type C）
    if r['id'] in ('rp-002', 'rp-005'):
        r['pci']['lesions'][0]['type'] = 'C'
    for l in r.get('pci', {}).get('lesions', []):
        if l.get('morph', {}).get('cto') == 'yes':
            l.setdefault('cto', {})['duration'] = '>=3m'
            # J-CTO 2（Blunt・屈曲 >45°）
            l['cto']['jcto'] = {'blunt': 'yes', 'calc': 'no', 'bend': 'yes', 'len20': 'no', 'retry': 'no'}

with open(os.path.join(OUT, 'patients.json'), 'w', encoding='utf-8') as f:
    json.dump(patients, f, ensure_ascii=False, indent=1)
with open(os.path.join(OUT, 'reports.json'), 'w', encoding='utf-8') as f:
    json.dump(reports, f, ensure_ascii=False, indent=1)
with open(os.path.join(OUT, 'masters.json'), 'w', encoding='utf-8') as f:
    json.dump(masters, f, ensure_ascii=False, indent=1)
print(len(patients), 'patients,', len(reports), 'reports')
